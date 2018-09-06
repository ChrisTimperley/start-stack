all: py3

py3:
	pyinstaller --clean -y .pyinstaller-bootstrap.py \
	  --name startcli3 \
	  --distpath bin \
	  --onefile \
	  --hidden-import cement \
	  --hidden-import flask_api \
	  --hidden-import cement.ext.ext_dummy \
	  --hidden-import cement.ext.ext_smtp \
	  --hidden-import cement.ext.ext_plugin \
	  --hidden-import cement.ext.ext_configparser \
	  --hidden-import cement.ext.ext_logging \
	  --hidden-import flask_api.parsers \
	  --hidden-import flask_api.renderers

clean:
	rm -rf bin/* build

.PHONY: clean py3 py2
