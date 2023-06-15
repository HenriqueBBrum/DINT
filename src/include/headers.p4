#define PKT_INSTANCE_TYPE_NORMAL 0
#define PKT_INSTANCE_TYPE_INGRESS_CLONE 1
#define PKT_INSTANCE_TYPE_EGRESS_CLONE 2
#define PKT_INSTANCE_TYPE_COALESCED 3
#define PKT_INSTANCE_TYPE_INGRESS_RECIRC 4
#define PKT_INSTANCE_TYPE_REPLICATION 5
#define PKT_INSTANCE_TYPE_RESUBMIT 6

#define MAX_FLOWS 65536 // Maximum number of flows
#define MAX_PORTS 10
#define MAX_HOPS 8 // Maximum number of hops of a telemetry packet

#define HEADERS_SZ 50 //  Ethernet no CRC (14) +  Telemetry (8) + IPv4 (20) + UDP (8)
#define TEL_H_SZ 8
#define TEL_DATA_SZ 17 // Size (B) of each tel_data header
#define UDP_LEN 8 // Size (B) of a UDP header


#define COPY_INDEX 0 // Used to copy metadata from a original packet to a cloned packet
#define REPORT_MIRROR_SESSION_ID 500 // Session for mirrored packets


const bit<8> TYPE_UDP = 0x11;
const bit<16> TYPE_IPV4 = 0x800;
const bit<16> TYPE_TELEMETRY = 0X6666; // Custom type for telemetry header


typedef bit<9>  egress_spec_t;
typedef bit<48> mac_addr_t;
typedef bit<32> ipv4_addr_t;
typedef bit<48> time_t;


/*************************************************************************
*********************** H E A D E R S  ***********************************
*************************************************************************/

// Ethernet protocol header
header ethernet_t {
    mac_addr_t dst_addr;
    mac_addr_t src_addr;
    bit<16>   ether_type;
}

// Telemetry header with general information about the telemtry being reported
header telemetry_t{
    bit<8> hop_cnt;
    bit<8> telemetry_data_sz;
    bit<16> next_header_type;
    bit<32> flow_id;
}

// Telemtry header with information about each flow and switch. Link usage is monitored
header telemetry_data_t{
    bit<1> bos;
    bit<7> sw_id;

    // monitoring values
    bit<32> amt_bytes;
    bit<48> last_time;
    bit<48> curr_time;
}

// IPv4 protocol header
header ipv4_t {
    bit<4>    version;
    bit<4>    ihl;
    bit<8>    tos;
    bit<16>   total_len;
    bit<16>   identification;
    bit<3>    flags;
    bit<13>   frag_offset;
    bit<8>    ttl;
    bit<8>    protocol;
    bit<16>   hdr_checksum;
    ipv4_addr_t src_addr;
    ipv4_addr_t dst_addr;
}

// UDP protocol header
header udp_t {
    bit<16> src_port;
    bit<16> dst_port;
    bit<16> len;
    bit<16> checksum;
}

// Metada of each packet during processing inside a switch
struct metadata {
    @field_list(COPY_INDEX)
    bit<1> insert_tel;

    bit<1> cloned;
    bit<7> sw_id;

    @field_list(COPY_INDEX)
    bit<32> flow_id;
    @field_list(COPY_INDEX)
    bit<48> last_time;
    @field_list(COPY_INDEX)
    bit<48> curr_time;
}

// Overall structure of a packet header
struct headers {
    ethernet_t   ethernet;
    telemetry_t telemetry;
    telemetry_data_t[MAX_HOPS]  tel_data;   // Header stack, one for each switch with a maximum of 'MAX_HOPS' elements
    ipv4_t       ipv4;
    udp_t        udp;
}
