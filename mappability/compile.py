
import sys, glob, re, subprocess

def run(cmd):
    print cmd
    if not dryrun:
        subprocess.call(cmd, shell=True)

def get_fa_basenames():
    pat=re.compile('(.+)\.fa')
    fl=glob.glob('*.fa')
    return [pat.match(f).group(1) for f in fl]

if __name__=='__main__':
    if len(sys.argv) != 2:
        print 'usage %s <merlen>' % sys.argv[0]
        sys.exit(1)
    merlen=sys.argv[1]
    fas = get_fa_basenames()
    dryrun=False
    
    for fa in fas:
        run('chr2hash %s.fa' % (fa))

    for fa1 in fas:
        for fa2 in fas:
            run('oligoFindPLFFile %s.fa %s.fa %s 0 0 1 1 > %sx%s.out' % (fa1, fa2, merlen, fa1, fa2))

    for fa in fas:
        run('mergeOligoCounts %s > %sb.out' % (' '.join(['%sx%s.out' % (f, fa) for f in fas]) , fa))
