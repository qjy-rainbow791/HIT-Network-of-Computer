/*
* THIS FILE IS FOR IP FORWARD TEST
*/
#include "sysInclude.h"
#include<map>

// system support
extern void fwd_LocalRcv(char *pBuffer, int length);

extern void fwd_SendtoLower(char *pBuffer, int length, unsigned int nexthop);

extern void fwd_DiscardPkt(char *pBuffer, int type);

extern unsigned int getIpv4Address( );

// implemented by students
// build the route table by map
map<unsigned int, unsigned int> routeTable;

void stud_Route_Init()
{
	routeTable.clear();
	return;
}

void stud_route_add(stud_route_msg *proute)
{
	unsigned int dest = ntohl(proute->dest)&(0xffffffff<<(32-htonl(proute->masklen)));
	unsigned int nexthop = ntohl(proute->nexthop);
	routeTable[dest] = nexthop;
	return;
}


int stud_fwd_deal(char *pBuffer, int length)
{
	int headLength = pBuffer[0] & 0xf;
	int TTL = (int)pBuffer[8];
	int checkSum = ntohl(*(short unsigned int*)(pBuffer + 10));
	int dstAddr = ntohl(*(unsigned int*)(pBuffer + 16));
	
	// recieved
	if (dstAddr == getIpv4Address()){
		fwd_LocalRcv(pBuffer, length);
		return 0;
	}
	
	// TTL error
	if (TTL <= 0){
		fwd_DiscardPkt(pBuffer, STUD_FORWARD_TEST_TTLERROR);
		return 1;
	}
	
	int dstcount = routeTable.count(dstAddr);
	map<unsigned int, unsigned int>::iterator nexthop;
	nexthop = routeTable.find(dstAddr);

	// no route error
	if (dstcount == 0){
		fwd_DiscardPkt(pBuffer, STUD_FORWARD_TEST_NOROUTE);
		return 1;
	}

	// transmit
	if (nexthop != routeTable.end()){
		char *sBuffer = new char[length];
		memcpy(sBuffer, pBuffer, length);
		// TTL-1
		sBuffer[8]--;
		// update checksum
		unsigned short newCheckSum = 0;
		unsigned short tempNum = 0;
		for (int i = 0; i < headLength * 2; i++){
			if (i != 5){
					tempNum = ((unsigned char)sBuffer[i*2]<<8) + (unsigned char)sBuffer[i*2+1];
					if (0xffff - newCheckSum < tempNum){
					newCheckSum = newCheckSum + tempNum + 1;
				}
					else{
					newCheckSum = newCheckSum + tempNum;
				}
			}
		}
		newCheckSum = htons(~newCheckSum);
		memcpy(sBuffer + 10, &newCheckSum, sizeof(unsigned short int));
		fwd_SendtoLower(sBuffer, length, nexthop->second);
		return 0;
	}
	return 0;
}
