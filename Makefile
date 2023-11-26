venv: venv/touchfile

venv/touchfile: requirements.txt
	test -d venv || virtualenv venv
	. venv/bin/activate; pip install -Ur requirements.txt
	touch venv/touchfile

run:
	source ./venv/bin/activate; python wizbaz/main.py

test: venv
	source ./venv/bin/activate; nosetests test 

clean:
	rm -rf venv 
	find -iname "*.pyc" -delete
