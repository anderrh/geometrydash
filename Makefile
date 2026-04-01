main.gb: main.asm $(wildcard include/*) $(wildcard *.asm)
	rgbasm -I include -o main.o main.asm
	rgbasm -o hUGEDriver.o hUGEDriver.asm
	rgbasm -I include -o menumusic.o menumusic.asm
	rgbasm -I include -o level2music.o level2music.asm
	rgbasm -I include -o level3music.o level3music.asm
	rgblink -o main.gb main.o hUGEDriver.o level3music.o level2music.o menumusic.o 
	rgbfix -v -p 0xFF -m MBC5 main.gb
	rgblink -n main.sym main.o hUGEDriver.o level3music.o level2music.o menumusic.o 
