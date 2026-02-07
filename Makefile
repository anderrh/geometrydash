main.gb: main.asm $(wildcard include/*) func.asm util.asm tiles.asm var.asm level.asm
	rgbasm -I include -o main.o main.asm
	rgbasm -o hUGEDriver.o hUGEDriver.asm
	rgblink -o main.gb main.o hUGEDriver.o
	rgbfix -v -p 0xFF -m MBC5 main.gb
	rgblink -n main.sym main.o hUGEDriver.o
