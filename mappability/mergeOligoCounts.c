#include <assert.h>
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <sys/types.h>

int
main(int argc, char *argv[])
{
  unsigned int	countCount = -1;
  int		i;
  unsigned char	*mergedCounts = 0;
  unsigned char	*mergedCountsEnd = 0;

  if (argc < 2) {
    fprintf(stderr, "Usage: %s <binary count table>+\n", argv[0]);
    exit(1);
  }

  for (i = 1; i < argc; ++i) {
    unsigned char	*counts;
    unsigned char	*cp;
    int			countFd;
    struct stat		countStats;
    unsigned char	*mcp;

    // load count table
    {
      assert(-1 != (countFd = open(argv[i], O_RDONLY)));
      assert(-1 != fstat(countFd, &countStats));
      assert(MAP_FAILED != (counts = (unsigned char *)mmap(0, countStats.st_size, PROT_READ, MAP_PRIVATE, countFd, 0)));
    }

    // if necessary, allocate merge buffer.
    if (!mergedCounts) {
      countCount = countStats.st_size;
      assert(mergedCounts = calloc(countCount, 1));
      mergedCountsEnd = mergedCounts + countCount;
    }
    else {
      if (countCount != countStats.st_size) {
	fprintf(stderr, "merged failed: %s differs in size.\n", argv[i]);
	exit(1);
      }
    }

    // merge the count data.
    for (cp = counts, mcp = mergedCounts; mcp < mergedCountsEnd; ++cp, ++mcp) {
      if (*cp) {
	unsigned int	sum;

	sum = *mcp + *cp;
	if (sum > 255)
	  *mcp = 255;
	else
	  *mcp = sum;
      }
    }

    // release the count file
    assert(-1 != munmap(counts, countCount));
    assert(-1 != close(countFd));
  }

  // dump the merged counts.
  assert(countCount == write(1, mergedCounts, countCount));

  return 0;
}

