# Lector del formato .msg de Yakuza 5 Remastered (big endian). Ver PASO_A_PASO.txt.
# Cabecera: u16 0x20F7, u16 ?, u32 0x18 (tabla de secciones), u32 fin_textos, u16 n_?, u16 n_?, u32, u32.
# Sección (16 bytes): u32 0, u32 off_registros, u16 n, u16 ?, u32 ?.
# Registro (12 bytes): u16 largo, u8 n_funciones, u8 0, u32 off_texto, u32 off_funciones.
# Función (16 bytes): u8 tipo, u8 sub, u16 valor, u32 posición (byte dentro del texto), u32, u32.
import struct
def leer(b):
    secs=[];o=0x18
    while True:
        z,off,cnt,a,c=struct.unpack('>IIHHI',b[o:o+16])
        if z!=0 or off<0x18 or off>len(b): break
        secs.append((o,off,cnt)); o+=16
        if o>=secs[0][1]: break
    regs=[]
    for so,off,cnt in secs:
        for i in range(cnt):
            r=off+12*i
            L,nf,y,t,p=struct.unpack('>HBBII',b[r:r+12])
            funcs=[(p+16*k,b[p+16*k:p+16*k+16]) for k in range(nf)]
            regs.append(dict(reg=r,L=L,nf=nf,y=y,t=t,p=p,texto=b[t:t+L],funcs=funcs))
    return secs,regs
