for ARGUMENT in "$@"
do

    KEY=$(echo $ARGUMENT | cut -f1 -d=)
    VALUE=$(echo $ARGUMENT | cut -f2 -d=)

    case "$KEY" in
            src_port)              src_port=${VALUE} ;;
            bw_rate)    bw_rate=${VALUE} ;;
            bw_ceil)   bw_ceil=${VALUE} ;;
            iface)  iface=${VALUE} ;;
            *)
    esac

done

#echo "DSTAT TO = $dstat"
#echo "REQUESTING = $req"
#echo "AB OP = $ab"

# $src_port=$1
# $bw_rate=$2 
# $bw_ceil=$3
# $iface=$4

tc qdisc del dev $iface root
tc qdisc add dev $iface root handle 1:0 htb default 10
tc class add dev $iface parent 1:0 classid 1:10 htb rate $bw_rate ceil $bw_ceil prio 0
iptables -A OUTPUT -t mangle -p tcp --sport $src_port -j MARK --set-mark 10
tc filter add dev $iface parent 1:0 prio 0 protocol ip handle 10 fw flowid 1:10

