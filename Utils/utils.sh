function latest() {
	glob=${1}
	latest=$(ls -t ${glob})
	latest=($latest)
	latest=${latest} #equivalent to ${latest[0]}
	echo $latest
}
