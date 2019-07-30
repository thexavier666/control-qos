for ARGUMENT in "$@"
do

    KEY=$(echo $ARGUMENT | cut -f1 -d=)
    VALUE=$(echo $ARGUMENT | cut -f2 -d=)   

    case "$KEY" in
            dstat)              dstat=${VALUE} ;;
            req)    req=${VALUE} ;;
	    fio)   fio=${VALUE} ;;
	    ab)  ab=${VALUE} ;;
            *)
    esac

done

#echo "DSTAT TO = $dstat"
#echo "REQUESTING = $req"
#echo "AB OP = $ab"

## FIO JOBFILE LOCATION : /mnt/shared_dir/job2.fio

ssh  -t kaustavc@10.5.20.124 "sh ~/PROJECT/ab_job.sh $req ~/PROJECT/$ab" &
ssh  -t kaustavc@10.5.20.81 "sh ~/fio_script.sh $dstat" >> ~/Desktop/KGP_Docker/PROJECT/fio_results/$fio

#ssh -t  kaustavc@10.5.20.124 "sh ~/ab_job.sh $req  $ab"
