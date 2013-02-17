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

typedef struct chromosome {
  int		fd;
  char		*name;
  long		offset;
  struct stat	stats;
} Chromosome;

int
main(int argc, char *argv[])
{
  int		bases;
  Chromosome	chr;
  unsigned char	*chrBuf;
  long		chrSize;
  int		hash;
  int		i;
  unsigned int	*offsetTable;
  long		ntCount;
  unsigned char	*pos;
  unsigned int	*posTable;
  long		total;

  assert(0 != (offsetTable = calloc(MerHashSize+1, sizeof(offsetTable[0]))));

  chr.name = argv[1];
  assert(-1 != (chr.fd = open(chr.name, O_RDONLY)));
  assert(-1 != fstat(chr.fd, &chr.stats));
  chrSize = chr.stats.st_size;

  assert(0 != (chrBuf = malloc(chrSize+1)));
  assert(chrSize == read(chr.fd, chrBuf, chrSize));
  chrBuf[chrSize] = 0;

  // skip first line.
  while (*chrBuf && ('\n' != *chrBuf++));

  // figure out population of each bin.
  bases = 0;
  hash = 0;
  for (pos = chrBuf; *pos; ++pos) {
    int	code;

    if ('\n' == *pos) continue;

    code = codings[*pos];

    if (-1 == code) {
      bases = 0;
      hash = 0;
      continue;
    }

    hash = ((hash << 2) | code) & MerHashMask;

    if (bases < MerSize) ++bases;

    if (MerSize == bases) ++offsetTable[hash];
  }

  // turn population into offset numbers
  total = 0;
  for (i = 0; i < MerHashSize; ++i) {
    int	newTotal = total + offsetTable[i];
    offsetTable[i] = total;
    total = newTotal;
  }
  offsetTable[MerHashSize] = total;

  // write out offset table
  {
    int		hptFd = -1;
    char	*name;
    int		numBytes = sizeof(offsetTable[0])*(MerHashSize+1);

    assert(0 != (name = malloc(strlen(argv[1])+strlen(OffsetFileSuffix)+1)));
    sprintf(name, "%s%s", argv[1], OffsetFileSuffix);
    assert((hptFd = open(name, O_WRONLY|O_CREAT, 0600)) >= 0);
    assert(numBytes == write(hptFd, offsetTable, numBytes));
    close(hptFd);
    free(name);
  }
	   
  assert(0 != (posTable = malloc(total * sizeof(posTable[0]))));

  // fill in position table
  bases = 0;
  hash = 0;
  ntCount = 0;
  for (pos = chrBuf; *pos; ++pos) {
    int	code;

    if ('\n' == *pos) continue;
    ++ntCount;

    code = codings[*pos];

    if (-1 == code) {
      bases = 0;
      hash = 0;
      continue;
    }

    hash = ((hash << 2) | code) & MerHashMask;

    if (bases < MerSize) ++bases;

    if (MerSize == bases) {
      posTable[offsetTable[hash]++] = ntCount -  MerSize;
    }
  }

  // write out position table
  {
    int		ptFd = -1;
    char	*name;
    int		numBytes = sizeof(posTable[0])*total;

    assert(0 != (name = malloc(strlen(argv[1])+strlen(PosFileSuffix)+1)));
    sprintf(name, "%s%s", argv[1], PosFileSuffix);
    assert((ptFd = open(name, O_WRONLY|O_CREAT, 0600)) >= 0);
    assert(numBytes == write(ptFd, posTable, numBytes));
    close(ptFd);
    free(name);
  }

  return 0;
}

