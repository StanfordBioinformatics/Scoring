#include <assert.h>
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <sys/types.h>

#include "chr2hash.h"
// memory mapped data

#define MaxTargetLength	100000

int min(int i0, int i1) { return (i0 < i1) ? i0 : i1; }

void
extractSequence(HashMMData *mmData, unsigned int pos, int len, unsigned char *buf)
{
  int	line;
  int	offset;
  char	*p;

  line = pos/mmData->chrLL;
  offset = pos - line*mmData->chrLL;

  p = mmData->chrStart + line*(mmData->chrLL+1) + offset;

  while(len--){
    if ('\n' == *p) ++p;
    *buf++ = *p++;
  }
}
   
int
findTarget(HashMMData *mmData, unsigned char *target, int targetLen, unsigned char *extract, unsigned char *originalTarget, int eAllowed, int eAdded, unsigned int id, int outputP)
{
  int		count;
  int		hash;
  int		i;
  unsigned int	leftHigh, leftLow;
  int		offset;
  unsigned int	*offsetTable = mmData->offsetTable;
  unsigned int	*posTable = mmData->posTable;
  unsigned int	rightHigh, rightLow;
  unsigned char	*stop = target + targetLen - MerSize;

  count = 0;
  hash = 0;
  for (i = 0; i < MerSize; ++i) {
    int	code = codings[target[i]];
    hash = ((hash << 2) | code) & MerHashMask;
  }
  leftLow = offsetTable[hash];
  leftHigh = offsetTable[hash+1];
  if (leftLow == leftHigh) return 0;

  offset = targetLen - MerSize;
  
  if (offset) {
    hash = 0;
    for (i = offset; i < (offset+MerSize); ++i) {
      int	code = codings[target[i]];
      if (code < 0) return 0;
      hash = ((hash << 2) | code) & MerHashMask;
    }
    rightLow = offsetTable[hash];
    rightHigh = offsetTable[hash+1];
    if (rightLow == rightHigh) return 0;

    while (1) {
      if (posTable[leftLow]+offset > posTable[rightLow]) {
	++rightLow;
      }
      else if (posTable[leftLow]+offset < posTable[rightLow]) {
	++leftLow;
      }
      else {
	int	eSeen = 0;
	// We know that the ends of extract and target agree for MerSize nts.
	unsigned char	*ep = extract+MerSize; 
	unsigned char	*tp = target+MerSize;

	if ((tp < stop) || outputP)
	  extractSequence(mmData, posTable[leftLow], targetLen, extract);

	while (tp < stop) {
          // Ignore case by mapping to lower.
	  if (((*tp++)|32) != ((*ep++)|32))
	    if (++eSeen > eAllowed) break;
	}
	if (eSeen <= eAllowed) {
	  ++count;
	  if (outputP) {
	    printf("%u\t%d\t%d\t%.*s\t%.*s\n", id, eSeen+eAdded, posTable[leftLow], targetLen, originalTarget, targetLen, extract);
	  }
	}
	++leftLow;
	++rightLow;
      }
      if (rightLow == rightHigh) break;
      if (leftLow == leftHigh) break;
    }
  }
  else {
    for (i = leftLow; i < leftHigh; ++i) {
      ++count;
      if (outputP) {
	extractSequence(mmData, posTable[i], targetLen, extract);
	printf("%u\t%d\t%d\t%.*s\t%.*s\n", id, eAdded, posTable[i], targetLen, originalTarget, targetLen, extract);
      }
    }
  }
  return count;
}

typedef int (*TargetIter)(unsigned char **, unsigned int *id);

// target iterator for file containing list of targets.
static unsigned char	targetBuf[MaxTargetLength];
static FILE		*targetFp;
static int		targetMerLength;

int
nextTargetLine(unsigned char **p, unsigned int *id)
{
  int			l;
  static unsigned int	lineCount = 0;

  *p = (void *)fgets((void *)targetBuf, MaxTargetLength, targetFp);

  if (!*p) return 0;

  l = strlen((char *)*p);
  if ('\n' != targetBuf[l-1]) {
    fprintf(stderr, "target beginning %.40s is too long. Too lazy to resync, so bailing.\n", targetBuf);
    exit(1);
  }
  *id = lineCount++;

  return (--l); // Ditch the newline
}

int
nextTargetScan(unsigned char **p, unsigned int *id)
{
  static unsigned int	position = 0;
  static int		scanLength = 0;
  static int		targetX = 0;

  while (1) {
    int	c = fgetc(targetFp);

    if (EOF == c) {
      // set this so we know how long the target was (for the final stretch of 0's)
      *p = NULL;
      *id = position - targetMerLength;
      return 0;
    }
    if ('\n' == c) continue;
    ++position;
    if ('N' == c) {
      scanLength = 0;
      targetX = 0;
      continue;
    }

    if (MaxTargetLength == targetX) {
      memmove(targetBuf, targetBuf+MaxTargetLength-scanLength, scanLength);
      targetX = scanLength;
    }
    targetBuf[targetX++] = c;
    ++scanLength;

    if (scanLength == targetMerLength) {
      *p = targetBuf+targetX-targetMerLength;
      *id = position - targetMerLength;
      // next loop, need one more mer.
      --scanLength;
      return targetMerLength;
    }
  }
}

TargetIter
initTargetIterator(char *fn, int merLength)
{
  // open file containing list of targets.
  assert(targetFp = fopen(fn, "r"));

  if (merLength < 0)
    return nextTargetLine;
  else {
    // assume an fa file.
    // skip def line
    while (1) {
      int	c = fgetc(targetFp);
      if (EOF == c || '\n' == c) break;
    }
    targetMerLength = merLength;

    return nextTargetScan;
  }
}

// To avoid stack problems, these large arrays are allocated in bss.
unsigned char	extract[MaxTargetLength];
unsigned char	mutatedTarget[MaxTargetLength];

int
main(int argc, char *argv[])
{
  int		binaryP;
  int		denseP;
  int		doSnp;
  unsigned int	id;
  HashMMData	mmData;
  TargetIter	nextTarget;
  int		outputP;
  unsigned int	prevId;
  unsigned char	*target;
  int		targetLen;

  int		chrFd, hptFd, ptFd;
  struct stat	chrStats, hptStats, ptStats;

  if (argc != 8) {
    fprintf(stderr, "Usage: %s <chromosome basename> <file containing list of targets> <mer length> SNPsP OuputHitsP DenseP BinaryP\n", argv[0]);
    exit(1);
  }
  doSnp = (argv[4][0] == '1');
  outputP = (argv[5][0] == '1');
  denseP = (argv[6][0] == '1');
  binaryP = (argv[7][0] == '1');

  // load hash offset table
  {
    char	*name;

    assert(0 != (name = malloc(strlen(argv[1])+strlen(OffsetFileSuffix)+1)));
    sprintf(name, "%s%s", argv[1], OffsetFileSuffix);
    assert(-1 != (hptFd = open(name, O_RDONLY)));
    assert(-1 != fstat(hptFd, &hptStats));
    assert(MAP_FAILED != (mmData.offsetTable = (unsigned int *)mmap(0, hptStats.st_size, PROT_READ, MAP_PRIVATE, hptFd, 0)));
    free(name);
  }

  // load pos table
  {
    char	*name;

    assert(0 != (name = malloc(strlen(argv[1])+strlen(PosFileSuffix)+1)));
    sprintf(name, "%s%s", argv[1], PosFileSuffix);
    assert(-1 != (ptFd = open(name, O_RDONLY)));
    assert(-1 != fstat(ptFd, &ptStats));
    assert(MAP_FAILED != (mmData.posTable = (unsigned int *)mmap(0, ptStats.st_size, PROT_READ, MAP_PRIVATE, ptFd, 0)));
    free(name);
  }

  // load chr
  {
    char	*chr;
    assert(-1 != (chrFd = open(argv[1], O_RDONLY)));
    assert(-1 != fstat(chrFd, &chrStats));
    assert(MAP_FAILED != (chr = (char *)mmap(0, chrStats.st_size, PROT_READ, MAP_PRIVATE, chrFd, 0)));
    
    // skip first line.
    while (*chr && ('\n' != *chr++));
    mmData.chrStart = chr;
    // compute line length.
    while (*chr && ('\n' != *chr++));
    mmData.chrLL = chr - mmData.chrStart - 1; // do not count the line retrurn.
  }

  nextTarget = initTargetIterator(argv[2], atoi(argv[3]));

  prevId = -1;
  while ((targetLen = nextTarget(&target, &id))) {
    assert(targetLen >= MerSize);
    extract[targetLen] = 0;

    if (doSnp) {
      int	doReMap = 1;
      int	exact;
      int	limit = 2*MerSize;
      int	l1, l2;
      int	mapDelta = targetLen - 2*MerSize; // amount to shift index by to move from left to right anchor mer.
      int	p1, p2;
      int	s1, s2;
      char	nts[] = "ACGT";
      int	snp1 = 0, snp2 = 0;

      // First find everything that has exact matches for endpoints and at most 2 errors in between.
      exact = findTarget(&mmData, target, targetLen, extract, target, 2, 0, id, outputP);

      if (targetLen <= limit) {
	limit = targetLen;
	doReMap = 0;
      }
    
      memcpy(mutatedTarget, target, targetLen+1);
      for (l1 = 0; l1 < limit; ++l1) {
	p1 = l1;
	if (doReMap && (p1 >= MerSize)) p1 += mapDelta;

	for (s1 = 0; s1 < 4; ++s1) {
	  char	c1 = mutatedTarget[p1];

	  if (c1 == nts[s1]) continue;

	  mutatedTarget[p1] = nts[s1];

	  snp1 += findTarget(&mmData, mutatedTarget, targetLen, extract, target, 1, 1, id, outputP);

	  for (l2 = l1+1; l2  < limit; ++l2) {
	    p2 = l2;
	    if (doReMap && (p2 >= MerSize)) p2 += mapDelta;

	    for (s2 = 0; s2 < 4; ++s2) {
	      char	c2 = mutatedTarget[p2];

	      if (c2 == nts[s2]) continue;

	      mutatedTarget[p2] = nts[s2];
	      snp2 += findTarget(&mmData, mutatedTarget, targetLen, extract, target, 0, 2, id, outputP);

	      mutatedTarget[p2] = c2;
	    }
	  }
	  mutatedTarget[p1] = c1;
	}
      }
      if (!outputP) {
	int	i;

	if (denseP) {
	  // generate null data for positions that did not yield valid mers.
	  for (i = prevId+1; i < id; ++i) {
	    if (binaryP) 
	      fprintf(stdout, "%c%c%c%c", 0, 0, 0, 0);
	    else
	      fprintf(stdout, "%u\t%d\t%d\t%d\t%d\n", i, 0, 0, 0, 0);
	  }
	}
	if (binaryP)
	  fprintf(stdout, "%c%c%c%c", min((exact+snp1+snp2), 255), min(exact, 255), min(snp1, 255), min(snp2, 255));
	else
	  fprintf(stdout, "%u\t%d\t%d\t%d\t%d\n", id, (exact+snp1+snp2), exact, snp1, snp2);
      }
    }
    else {
      int count = findTarget(&mmData, target, targetLen, extract, target, 0, 0, id, outputP);
      if (!outputP) {
	int i;

	if (denseP) {
	  // generate null data for positions that did not yield valid mers.
	  for (i = prevId+1; i < id; ++i) {
	    if (binaryP)
	      fprintf(stdout, "%c", 0);
	    else
	      fprintf(stdout, "%u\t%d\n", i, 0);
	  }
	}
	if (binaryP)
	  fprintf(stdout, "%c", min(count, 255));
	else
	  fprintf(stdout, "%u\t%d\n", id, count);
      }
    }
    prevId = id;
  }

  if (!outputP && denseP) {
    int i;
    // generate null data for positions that did not yield valid mers.
    for (i = prevId+1; i <= id; ++i) {
      if (binaryP)
	fprintf(stdout, "%c", 0);
      else
	fprintf(stdout, "%u\t%d\n", i, 0);
    }
  }

  return 0;
}

