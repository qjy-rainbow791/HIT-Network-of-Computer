/*
* THIS FILE IS FOR IP TEST
*/
// system support
#include "sysInclude.h"

extern void ip_DiscardPkt(char* pBuffer,int type);

extern void ip_SendtoLower(char*pBuffer,int length);

extern void ip_SendtoUp(char *pBuffer,int length);

extern unsigned int getIpv4Address();

// implemented by students

int stud_ip_recv(char *pBuffer,unsigned short length)
{
	int version = pBuffer[0] >> 4;
	int headLength = pBuffer[0] & 0xf;
	int TTL = (unsigned short)pBuffer[8];
	int checkSum = ntohs(*(unsigned short *)(pBuffer + 10));
	int dstAddr = ntohl(*(unsigned int*)(pBuffer + 16));

	// version error
	if (version != 4){
		ip_DiscardPkt(pBuffer, STUD_IP_TEST_VERSION_ERROR);
		return 1;
	}
	
	// head length error
	if (headLength < 5){
		ip_DiscardPkt(pBuffer, STUD_IP_TEST_HEADLEN_ERROR);
		return 1;
	}

	// destination error
	if (dstAddr != getIpv4Address() && dstAddr != 0xffff){	// && broadcast address
		ip_DiscardPkt(pBuffer, STUD_IP_TEST_DESTINATION_ERROR);
		return 1;
	}

	// TTL error
	if (TTL <= 0){
		ip_DiscardPkt(pBuffer, STUD_IP_TEST_TTL_ERROR);
		return 1;
	}

	// checksum error
	unsigned short tempNum = 0;
	unsigned short sum = 0;
	for (int i = 0; i < headLength * 2; i++){
		tempNum = ((unsigned char)pBuffer[i*2]<<8) + (unsigned char)pBuffer[i*2+1];
		// overflow
		if (0xffff - sum < tempNum)
			sum = sum + tempNum + 1;
		else
			sum = sum + tempNum;
	}
	if (sum != 0xffff){
		ip_DiscardPkt(pBuffer, STUD_IP_TEST_CHECKSUM_ERROR);
		return 1;
	}

	// success to recieve
	ip_SendtoUp(pBuffer, length);
	return 0;
}

int stud_ip_Upsend(char *pBuffer,unsigned short len,unsigned int srcAddr,
				   unsigned int dstAddr,byte protocol,byte ttl)
{
	char *ipBuffer = (char *)malloc((20 + len) * sizeof(char));
	memset(ipBuffer, 0, len + 20);
	ipBuffer[0] = 0x45;	// version + headlength
	unsigned short totalLength = htons(len + 20);	// total length
	memcpy(ipBuffer + 2, &totalLength, 2);
	ipBuffer[8] = ttl;
	ipBuffer[9] = protocol;

	unsigned int src = htonl(srcAddr);
	unsigned int dst = htonl(dstAddr);
	memcpy(ipBuffer + 12, &src, 4);
	memcpy(ipBuffer + 16, &dst, 4);

	unsigned short sum = 0;
	unsigned short tempNum = 0;
	unsigned short checkSum = 0;	// set 0

	// check checksum
	for (int i = 0; i < 10; i++){
		tempNum = ((unsigned char)ipBuffer[i*2]<<8) + (unsigned char)ipBuffer[i*2+1];
		if(0xffff - sum < tempNum)
			sum = sum + tempNum + 1;
		else
			sum = sum + tempNum;
	}
	checkSum = htons(0xffff - sum);
	memcpy(ipBuffer + 10, &checkSum, 2);
	memcpy(ipBuffer + 20, pBuffer, len);
	ip_SendtoLower(ipBuffer, len + 20);
	return 0;
}
