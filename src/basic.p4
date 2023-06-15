/* -*- P4_16 -*- */
#include <core.p4>
#include <v1model.p4>

#include "include/headers.p4"
#include "include/parsers.p4"
#include "include/checksum.p4"



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
          }
      }
    }
}

/*************************************************************************
****************  E G R E S S   P R O C E S S I N G   *******************
*************************************************************************/


control MyEgress(inout headers hdr,
                 inout metadata meta,
                 inout standard_metadata_t standard_metadata) {
    apply{}
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
