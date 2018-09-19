%.asc: %
	gpg --default-key FF91E0BD --armor --detach-sign $<
	@./pluginfo

all: $(shell echo *.py | sed -e s/.py/.py.asc/g)
