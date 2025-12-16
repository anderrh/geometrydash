main.gb: main.asm hardware.inc func.asm util.asm tiles.asm var.asm startlevel.asm level.asm
	rgbasm -o main.o main.asm
	rgblink -o main.gb main.o
	rgbfix -v -p 0xFF main.gb
	rgblink -n main.sym main.o
