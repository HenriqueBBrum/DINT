/* -*- P4_16 -*- */
#include <core.p4>
#include <v1model.p4>

#include "include/headers.p4"
#include "include/parsers.p4"
#include "include/checksum.p4"

/***************************************************************/

const bit<48> tel_insertion_min_window = 1000000;
const bit<48> obs_window = 1000000; // 1 Seg = 1000000 microseg
const bit<48> max_t = 5000000;

const bit<48> alpha_1 = 9;
const bit<8> alpha_2 = 3; //shift divisor


const bit<32> k = 16;
const bit<8> div_shift = 4;

/***************************************************************/

const bit<64> div = 0x1999999A; /// Used to divide a number by 10
const bit<64> div_100 = 0x28F5C29;



const bit<32> base_delta = 300;


/*************************************************************************
*********************** R E G I S T E R S  *******************************
*************************************************************************/

register<bit<32>>(MAX_FLOWS) pres_byte_cnt_reg; // Used to check if there was a big enough variation (changes every obs_window)
register<bit<32>>(MAX_FLOWS) telemetry_byte_cnt_reg; // Used to save byte count information to telemetry header (changes every tel_insertion_min_window)
register<bit<32>>(MAX_FLOWS) past_byte_cnt_reg;
register<bit<32>>(MAX_FLOWS) packets_cnt_reg;

register<time_t>(MAX_FLOWS) previous_insertion_reg;
register<time_t>(MAX_FLOWS) obs_last_seen_reg;
register<time_t>(MAX_FLOWS) tel_insertion_window_reg;

register<bit<32>>(MAX_FLOWS) delta_reg;
register<bit<32>>(MAX_FLOWS) n_last_values_reg;
register<bit<32>>(MAX_FLOWS) count_reg;



time_t max(in time_t v1,in time_t v2){
    if(v1 > v2) return v1;
    else return v2;
}

time_t min(in time_t v1, in time_t v2){
    if(v1 < v2) return v1;
    else return v2;
}



/*************************************************************************
**************  I N G R E S S   P R O C E S S I N G   *******************
*************************************************************************/


/* Updates the dynamic threshold according to the SIMPLE MOVING AVERAGE function of the last k measured throughputs */
void update_delta(inout bit<32> flow_id, in bit<32> comparator, inout bit<32> delta){
    bit<32> ct; bit<32> sum;
    count_reg.read(ct, flow_id);
    n_last_values_reg.read(sum, flow_id);

    if(ct==k){
        bit<32> mean; bit<32> old_m;
        mean = sum >> div_shift;

        delta = (bit<32>)((div*(bit<64>)mean)>>32);

        delta_reg.write(flow_id, delta);
        sum = 0;
        ct = 0;
    }

    sum = sum + comparator; ct = ct + 1;

    n_last_values_reg.write(flow_id, sum);
    count_reg.write(flow_id, ct);
}



/* Updates the telemetry insertion period according by comparing the
   the difference in bytes between the current and previous observation window with a dynamic threshold (delta)  */
void update_telemetry_insertion_time(inout bit<32> flow_id, inout standard_metadata_t standard_metadata,
                                in bit<32> pres_amt_bytes, inout bit<32> delta){
    time_t obs_last_seen; time_t tel_insertion_window;

    obs_last_seen_reg.read(obs_last_seen, flow_id);
    tel_insertion_window_reg.read(tel_insertion_window, flow_id);
    if(tel_insertion_window == 0){
        tel_insertion_window = tel_insertion_min_window;
        tel_insertion_window_reg.write(flow_id, tel_insertion_window);
    }

    bit<32> past_amt_bytes;
    past_byte_cnt_reg.read(past_amt_bytes, flow_id);

    time_t now = standard_metadata.ingress_global_timestamp;
    if(obs_last_seen == 0){
        obs_last_seen = now;
        obs_last_seen_reg.write(flow_id, now);
    }

    if(now - obs_last_seen >= obs_window){
        int<32> delta_bytes = (int<32>)pres_amt_bytes - (int<32>)past_amt_bytes;
        if(delta_bytes > (int<32>)delta || delta_bytes < -1*((int<32>)delta)){
            tel_insertion_window = tel_insertion_min_window; // Decreases time if bytes difference was bigger than expected
        }else{
            tel_insertion_window = min(max_t, (tel_insertion_window*alpha_1)>>alpha_2); // Increases time if bytes difference was smaller than expected
        }

        /* Updates the dynamic threshold (delta) */
        update_delta(flow_id, pres_amt_bytes, delta);

        past_byte_cnt_reg.write(flow_id, pres_amt_bytes);
        pres_byte_cnt_reg.write(flow_id, 0);

        tel_insertion_window_reg.write(flow_id, tel_insertion_window);
        obs_last_seen_reg.write(flow_id, now);
    }
}


control MyIngress(inout headers hdr,
                  inout metadata meta,
                  inout standard_metadata_t standard_metadata){

    action drop() {
        mark_to_drop(standard_metadata);
    }

    action ipv4_forward(mac_addr_t dst_addr, egress_spec_t port){
        standard_metadata.egress_spec = port;
        hdr.ethernet.src_addr = hdr.ethernet.dst_addr;
        hdr.ethernet.dst_addr = dst_addr;
        hdr.ipv4.ttl = hdr.ipv4.ttl - 1;
    }

    table ipv4_lpm{
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


    /* Five tuple hash of src IP, src port, dst IP, dst port, and protocol. Indicates a flow */
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

    apply{
        if (hdr.ipv4.isValid()){
            ipv4_lpm.apply();

            /* Evaluation is done only with UPD packets for simplicity */
            if(hdr.udp.isValid()){
                five_tuple_hash();

                bit<32> amt_packets;
                bit<32> tel_amt_bytes;
                bit<32> total_amt_bytes;

                packets_cnt_reg.read(amt_packets, meta.flow_id);
                amt_packets = amt_packets+1;
                packets_cnt_reg.write(meta.flow_id, amt_packets);

                pres_byte_cnt_reg.read(total_amt_bytes, meta.flow_id);  // Used for the update function
                total_amt_bytes = total_amt_bytes+standard_metadata.packet_length;
                pres_byte_cnt_reg.write(meta.flow_id,  total_amt_bytes);

                telemetry_byte_cnt_reg.read(tel_amt_bytes, meta.flow_id);   // Used for telemetry purposes
                tel_amt_bytes = tel_amt_bytes+standard_metadata.packet_length;
                telemetry_byte_cnt_reg.write(meta.flow_id,  tel_amt_bytes);

                bit<32> delta = 0;
                delta_reg.read(delta, meta.flow_id);
                if(delta == 0){
                    delta = base_delta;
                    delta_reg.write(meta.flow_id, delta);
                }

                /* This is the observation window, where the tel_insertion_window value is updated*/
                update_telemetry_insertion_time(meta.flow_id, standard_metadata, total_amt_bytes, delta);

                time_t previous_insertion; time_t tel_insertion_window;
                previous_insertion_reg.read(previous_insertion, meta.flow_id);
                tel_insertion_window_reg.read(tel_insertion_window, meta.flow_id);

                time_t now = standard_metadata.ingress_global_timestamp;
                if(previous_insertion == 0){
                    previous_insertion = now;
                    previous_insertion_reg.write(meta.flow_id, now);
                }

                /* If the telemetry insertion has elapsed, save the timestamp of the previous and current insertion for the egress pipeline */
                if(now - previous_insertion >= tel_insertion_window){
                    meta.insert_tel = 1;

                    meta.last_time = previous_insertion;
                    meta.curr_time = now;
                    previous_insertion_reg.write(meta.flow_id, now);
                }

                /* If there is a telemetry header or one will be added, check if this is the final switch before the final destination host
                   In case it is, copy the packet to the egress pipeline, where the telemetry info is sent to the monitoring host */
                if(hdr.telemetry.isValid() || meta.insert_tel == 1)
                    clone_I2E.apply();
            }
        }
    }
}

/*************************************************************************
****************  E G R E S S   P R O C E S S I N G   *******************
*************************************************************************/

/* If necessary adds a telemtry header to a packet, otherwise this
   function adds a telemetry metadata header to a packet's telemetry metadata header stack */
void insert_telemetry(inout headers hdr, inout metadata meta, in bit<32> tel_amt_bytes){
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

            /* First header stack? Yes? Bottom of Stack */
            if (hdr.telemetry.hop_cnt == 1)
                hdr.tel_data[0].bos = 1;
            else
                hdr.tel_data[0].bos = 0;

            hdr.tel_data[0].sw_id = meta.sw_id;
            if(hdr.telemetry.hop_cnt>1)
                hdr.tel_data[0].amt_bytes = tel_amt_bytes - (bit<32>)(hdr.telemetry.hop_cnt-1)*(TEL_DATA_SZ) - TEL_H_SZ;
            else
                hdr.tel_data[0].amt_bytes = tel_amt_bytes;

            hdr.tel_data[0].last_time = meta.last_time;
            hdr.tel_data[0].curr_time = meta.curr_time;

            telemetry_byte_cnt_reg.write(meta.flow_id, 0);
        }
}


control MyEgress(inout headers hdr,
                 inout metadata meta,
                 inout standard_metadata_t standard_metadata){

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
            sw_id.apply(); // Get this switch's ID

            bit<32> tel_bytes;
            telemetry_byte_cnt_reg.read(tel_bytes, meta.flow_id);

            /* Removes payload from cloned packet, adjusts IPv4 and UDP length fields, and send to the monitoring host */
            if(standard_metadata.instance_type == PKT_INSTANCE_TYPE_INGRESS_CLONE){
                clone_lpm.apply();

                 /** Collects metadata */
                if(meta.insert_tel == 1)
                    insert_telemetry(hdr, meta, tel_bytes);

                bit<32> truncate_sz = HEADERS_SZ+(bit<32>)hdr.telemetry.hop_cnt*TEL_DATA_SZ;

                truncate(truncate_sz); // Remove user data from clone packet
                hdr.ipv4.total_len = 28;
                hdr.udp.len = 8;
            }else if(standard_metadata.instance_type == PKT_INSTANCE_TYPE_NORMAL){
                // If switch is a transit switch, check if telemetry needs to be added
                // If its a sink switch, remove telemetry headers
                if(meta.cloned == 0 && meta.insert_tel == 1)
                    insert_telemetry(hdr, meta, tel_bytes);
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
