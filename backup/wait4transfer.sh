TMP="./xxxtransferdata.zip"
URL=https://raw.githubusercontent.com/pkhopper/vavava/master/vavava/transfer.py

if [ ! -f "./transfer.py" ]; then
  wget $URL
fi

if [! -f "$TMP" ]; then
  rm $TMP
fi

python transfer.py --force --server --ip 0.0.0.0 --port 1237 --outputfile $TMP

unzip $TMP
