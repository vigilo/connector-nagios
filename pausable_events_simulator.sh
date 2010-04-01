#!/bin/bash
if [[ "$1" == "--help" || "$1" == "-h" ]] ; then
    exit 0
fi

# les états nagios
STATE=(CRITICAL WARNING UNKNOWN OK OK)
# les services supervisés
# L'entrée '' permet d'envoyer des alertes sur les hôtes directement.
INDICATEUR=('Interface eth0' 'Interface eth1' 'Interface eth2' '' 'HTTPd' 'CPU' 'Processes' 'Load' 'UpTime')
# la liste des serveurs
# La valeur 'HLS' est réservée et correspond
# aux services de haut niveau (High-Level Services).
SERVER=(host2.example.com host1.example.com proto4 messagerie brouteur)


function random() {
    rand=$RANDOM
    MIN=$1
    MAX=$2
    MAX=$(($MAX + 1))
    let "rand %= $MAX"
    while [ "$rand" -lt $MIN ]; do 
        rand=$RANDOM
        let "rand %= $MAX"  # Scales $rand down within $MAX.
    done
    echo $rand
}

function random_wait() {
    seconde_waited=`random 10 20`
    sleep $seconde_waited
}

function random_state () {
    min=0
    max=${#STATE[@]}
    max=$(($max - 1))
    random=`random $min $max`
    echo -n ${STATE[$random]}
}

function random_indicateur () {
    min=0
    max=${#INDICATEUR[@]}
    max=$(($max - 1))
    random=`random $min $max`
    echo -n ${INDICATEUR[$random]}
}

function random_serveur () {
    min=0
    max=${#SERVER[@]}
    max=$(($max - 1))
    random=`random $min $max`
    echo -n ${SERVER[$random]}
}

seconde=`date +%s`
while true; do 
    seconde=`date +%s`
#    seconde=$(($seconde+`random 1 86400`))
    value=`random 0 100`
    ind=`random_indicateur`
    ser=`random_serveur`
    ser_name=`echo $ser | awk -F" " '{ print $1 }'`
    sta=`random_state`
    echo "event|$seconde|$ser_name|$ind|$sta|$sta:  $ind:  $value  $value  $value"
    echo "Please press Enter to send a new event..." >&2
    read pause
done

