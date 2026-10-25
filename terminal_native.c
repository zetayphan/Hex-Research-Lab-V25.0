#include <stdint.h>
#include <stddef.h>
#define MASK 0xFFFFFFu
/* All operations use unsigned 24-bit hexadecimal words. */
int hex_terminal_eval(uint32_t a,uint32_t b,int op,uint32_t *out){
 if(!out)return -1;
 a &= MASK;b &= MASK;
 switch(op){
 case 0:*out=(a+b)&MASK;break;
 case 1:*out=(a-b)&MASK;break;
 case 2:*out=(a*b)&MASK;break;
 case 3:*out=a^b;break;
 case 4:*out=a&b;break;
 case 5:*out=a|b;break;
 case 6:*out=((a<<(b%24))|(a>>((24-(b%24))%24)))&MASK;break;
 case 7:*out=((a>>(b%24))|(a<<((24-(b%24))%24)))&MASK;break;
 case 8:if(!b)return -2;*out=a/b;break;
 case 9:if(!b)return -2;*out=a%b;break;
 default:return -3;
 }
 return 0;
}
