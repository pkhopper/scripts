
curl -o "wait4transfer.sh" "https://raw.githubusercontent.com/pkhopper/scripts/master/backup/wait4transfer.sh"

if [ ! -d "$HOME/local" ]; then
	mkdir "$HOME/local"
fi

if [ ! -d "$HOME/local/share" ]; then
	mkdir "$HOME/local/share"
fi

if [ ! -f "$HOME/local/share/config.site" ]; then
	echo "CPPFLAGS=-I$HOME/local/include 
	LDFLAGS=-L$HOME/local/lib" > "$HOME/local/share/config.site"
fi

echo "download Python-2.7.12.tgz"
if [ ! -f "Python-2.7.12.tgz" ]; then
	curl "https://www.python.org/ftp/python/2.7.12/Python-2.7.12.tgz" -o Python-2.7.12.tgz
fi
tar vxf "Python-2.7.12.tgz"
cd Python-2.7.12
./configure --prefix="$HOME/local"
make clean
make
make install
cd ..


PATH=$HOME/local/bin:$PATH
EXPORT $PATH


echo "download setuptools-26.0.0.tar.gz"
if [ ! -f "setuptools-26.0.0.tar.gz" ]; then
	curl "https://pypi.python.org/packages/0d/13/ce6a0a22220f3da7483131bb8212d5791a03c8c3e86ff61b2c6a2de547cd/setuptools-26.0.0.tar.gz#md5=846e21fea62b9a70dfc845d70c400b7e" -o setuptools-26.0.0.tar.gz
fi
tar vxf "setuptools-26.0.0.tar.gz"
cd "setuptools-26.0.0"
python setup.py install
cd ..


echo "download django.1.9.4.tar.gz"
if [ ! -f "django.1.9.4.tar.gz" ]; then
	curl "https://github.com/django/django/archive/1.9.4.tar.gz"  -o django.1.9.4.tar.gz
fi
tar vxf "django.1.9.4.tar.gz"
cd "django"
python setup.py install
cd ..


echo "download supervisor"
if [ ! -d "supervisor" ]; then
	git clone "https://github.com/Supervisor/supervisor.git"
fi
cd "supervisor"
python setup.py install
cd ..

