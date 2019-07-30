for ARGUMENT in "$@"
do

    KEY=$(echo $ARGUMENT | cut -f1 -d=)
    VALUE=$(echo $ARGUMENT | cut -f2 -d=)   

    case "$KEY" in
            cont_name)   cont_name=${VALUE} ;;
            from)    from=${VALUE} ;;
            to)   to=${VALUE} ;;
            *)
    esac

done

# EXAMPLE => moving ab server from :124 to :81 
# echo kaustav123 | ssh -tt kaustavc@10.5.20.124 "sudo docker stop xenodochial_wilson"
# echo kaustav123 | ssh -tt kaustavc@10.5.20.81 "sudo docker run -dP -it --name xenodochial_wilson ab_server:v4"

echo kaustav123 | ssh -tt kaustavc@10.5.20.$from "sudo docker stop $cont_name"
echo kaustav123 | ssh -tt kaustavc@10.5.20.$to "sudo docker run -dP -it -p {}:80 --name $cont_name ab_server:v4"
		
