/* -*- P4_16 -*- */
#include <core.p4>
#include <v1model.p4>

#include "include/headers.p4"
#include "include/parsers.p4"
#include "include/checksum.p4"

const bit<48> tel_insertion_window = 1000000; // 1 Seg = 1000000 microseg


/*************************************************************************
*********************** R E G I S T E R S  ***********************************
*************************************************************************/


register<bit<32>>(MAX_FLOWS) pres_byte_cnt_reg;
register<bit<32>>(MAX_FLOWS) packets_cnt_reg;

register<time_t>(MAX_FLOWS) previous_insertion_reg;


/*************************************************************************
**************  I N G R E S S   P R O C E S S I N G   *******************
*************************************************************************/


control MyIngress(inout headers hdr,
                  inout metadata meta,
                  inout standard_metadata_t standard_metadata) {

    action drop() {
        mark_to_drop(standard_metadata);
    }

    action ipv4_forward(mac_addr_t dst_addr, egress_spec_t port) {
        standard_metadata.egress_spec = port;
        hdr.ethernet.src_addr = hdr.ethernet.dst_addr;
        hdr.ethernet.dst_addr = dst_addr;
        hdr.ipv4.ttl = hdr.ipv4.ttl - 1;
    }

    table ipv4_lpm {
        key = {
            hdr.ipv4.dst_addr: lpm;
        }
        actions = {
            ipv4_forward;
            drop;
            NoAction;
        }
        size = 1024;
        default_action = drop();
    }

    action clone_pkt() {
        meta.cloned = 1;
        clone_preserving_field_list(CloneType.I2E, REPORT_MIRROR_SESSION_ID, COPY_INDEX);
    }

    table clone_I2E{
        key = {
            hdr.ipv4.dst_addr: lpm;
        }
        actions = {
            clone_pkt;
            NoAction;
        }
        size = 1024;
    }


    action five_tuple_hash(){
        hash(meta.flow_id,
        HashAlgorithm.crc16,
        (bit<16>)0,
        {
            hdr.ipv4.src_addr,
            hdr.udp.src_port,
            hdr.ipv4.dst_addr,
            hdr.udp.dst_port,
            hdr.ipv4.protocol
        },
        (bit<16>)0XFFFF
        );
    }

    apply {
        if (hdr.ipv4.isValid()){
            ipv4_lpm.apply();
            if(hdr.udp.isValid()){
                five_tuple_hash();

                bit<32> amt_packets;
                bit<32> amt_bytes;

                packets_cnt_reg.read(amt_packets, meta.flow_id);
                amt_packets = amt_packets+1;
                packets_cnt_reg.write(meta.flow_id, amt_packets);

                pres_byte_cnt_reg.read(amt_bytes, meta.flow_id);
                amt_bytes = amt_bytes+standard_metadata.packet_length;
                pres_byte_cnt_reg.write(meta.flow_id,  amt_bytes);

                time_t previous_insertion;
                previous_insertion_reg.read(previous_insertion, meta.flow_id);

                time_t now = standard_metadata.ingress_global_timestamp;
                if(previous_insertion == 0){
                    previous_insertion = now;
                    previous_insertion_reg.write(meta.flow_id, now);
                }

                if(now - previous_insertion >= tel_insertion_window){
                    meta.insert_tel = 1;

                    meta.last_time = previous_insertion;
                    meta.curr_time = now;
                    previous_insertion_reg.write(meta.flow_id, now);
                }

                if(hdr.telemetry.isValid() || meta.insert_tel == 1)
                    clone_I2E.apply();
            }
        }
    }
}

/*************************************************************************
****************  E G R E S S   P R O C E S S I N G   *******************
*************************************************************************/


void insert_telemetry(inout headers hdr, inout metadata meta, in bit<32> pres_amt_bytes){
        if(!hdr.telemetry.isValid()){
            hdr.ethernet.ether_type = TYPE_TELEMETRY;

            hdr.telemetry.setValid();
            hdr.telemetry.hop_cnt = 0;
            hdr.telemetry.next_header_type = TYPE_IPV4;
            hdr.telemetry.telemetry_data_sz = TEL_DATA_SZ;
            hdr.telemetry.flow_id = meta.flow_id;
        }

        if(hdr.telemetry.hop_cnt < MAX_HOPS){
            hdr.telemetry.hop_cnt = hdr.telemetry.hop_cnt + 1;

            hdr.tel_data.push_front(1);
            hdr.tel_data[0].setValid();

            if (hdr.telemetry.hop_cnt == 1)
                hdr.tel_data[0].bos = 1;
            else
                hdr.tel_data[0].bos = 0;

            hdr.tel_data[0].sw_id = meta.sw_id;
            if(hdr.telemetry.hop_cnt>1)
                hdr.tel_data[0].amt_bytes = pres_amt_bytes - (bit<32>)(hdr.telemetry.hop_cnt-1)*(TEL_DATA_SZ) - TEL_H_SZ;
            else
                hdr.tel_data[0].amt_bytes = pres_amt_bytes;

            hdr.tel_data[0].last_time = meta.last_time;
            hdr.tel_data[0].curr_time = meta.curr_time; // (bit<64>)(now - previous_insertion);

            pres_byte_cnt_reg.write(meta.flow_id, 0);
        }
}



control MyEgress(inout headers hdr,
                 inout metadata meta,
                 inout standard_metadata_t standard_metadata) {

    action set_sw_id(bit<7> sw_id){
        meta.sw_id = sw_id;
    }

    table sw_id{
        actions = {
            set_sw_id;
            NoAction;
        }

        default_action = NoAction();
    }


    action drop() {
        mark_to_drop(standard_metadata);
    }


    action clone_forward(mac_addr_t dst_addr, egress_spec_t port){
        hdr.ethernet.src_addr = hdr.ethernet.dst_addr;
        hdr.ethernet.dst_addr = dst_addr;
        standard_metadata.egress_spec = port;
        hdr.ipv4.ttl = hdr.ipv4.ttl - 1;
    }


    table clone_lpm{
        key = {
            hdr.ipv4.dst_addr: lpm;
        }
        actions = {
            clone_forward;
            drop;
            NoAction;
        }
        size = 1024;
        default_action = drop();
    }


    apply{
        if(hdr.ipv4.isValid() && hdr.udp.isValid()){
            sw_id.apply();

            bit<32> amt_bytes;
            pres_byte_cnt_reg.read(amt_bytes, meta.flow_id);

            if(standard_metadata.instance_type == PKT_INSTANCE_TYPE_INGRESS_CLONE){
                clone_lpm.apply();

                 /** Collects metadata */
                if(meta.insert_tel == 1)
                    insert_telemetry(hdr, meta, amt_bytes);

                bit<32> truncate_sz = HEADERS_SZ+(bit<32>)hdr.telemetry.hop_cnt*TEL_DATA_SZ;

                truncate(truncate_sz); // Remove user data from clone packet
                hdr.ipv4.total_len = 28;
                hdr.udp.len = 8;
            }else if(standard_metadata.instance_type == PKT_INSTANCE_TYPE_NORMAL){
                // If switch is a transit switch, check if telemetry needs to be added
                // If its a sink switch, remove telemetry headers
                if(meta.cloned == 0 && meta.insert_tel == 1)
                    insert_telemetry(hdr, meta, amt_bytes);
                else if(meta.cloned == 1){
                    hdr.telemetry.setInvalid();
                    hdr.tel_data.pop_front(MAX_HOPS);
                    hdr.ethernet.ether_type = TYPE_IPV4;
                }
            }
        }
    }
}



/*************************************************************************
***********************  S W I T C H  *******************************
*************************************************************************/

V1Switch(
MyParser(),
MyVerifyChecksum(),
MyIngress(),
MyEgress(),
MyComputeChecksum(),
MyDeparser()
) main;
