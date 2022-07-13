/*************************************************************************
*********************** P A R S E R  ***********************************
*************************************************************************/



parser MyParser(packet_in packet,
                out headers hdr,
                inout metadata meta,
                inout standard_metadata_t standard_metadata) {

    state start {
        transition parse_ethernet;
    }

    state parse_ethernet {
        packet.extract(hdr.ethernet);
        transition select(hdr.ethernet.ether_type) {
            TYPE_TELEMETRY: parse_telemetry;
            TYPE_IPV4: parse_ipv4;
            default: accept;
        }
    }

    state parse_telemetry {
        packet.extract(hdr.telemetry);
        transition select(hdr.telemetry.hop_cnt) {
            0: parse_ipv4;
            default: parse_tel_data;
        }
    }

    state parse_tel_data {
        packet.extract(hdr.tel_data.next);
        transition select(hdr.tel_data.last.bos) {
            1: parse_ipv4;
            default: parse_tel_data;
        }
    }

    state parse_ipv4{
        packet.extract(hdr.ipv4);
        transition select(hdr.ipv4.protocol) {
            TYPE_UDP: parse_udp;
            default: accept;
        }
    }

    state parse_udp{
        packet.extract(hdr.udp);
        transition accept;
    }

}




/*************************************************************************
***********************  D E P A R S E R  *******************************
*************************************************************************/

control MyDeparser(packet_out packet, in headers hdr){
    apply {
        packet.emit(hdr);
    }
}
