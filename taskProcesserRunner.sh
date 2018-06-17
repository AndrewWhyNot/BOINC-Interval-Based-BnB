#/bin/sh

while [ true ]; do
	res=$(/usr/bin/python3 taskProcesser.py 2>&1 >> out)
	#res = $($res: -1)
	echo $res
	if [ "$res" -eq "0" ]
	then
		exit 0
	fi
	sleep $res
done
