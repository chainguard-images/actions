package main

import (
	"flag"
	"fmt"
	"os"
	"regexp"
	"strings"
	"sync"

	"github.com/google/go-containerregistry/pkg/crane"
	"github.com/google/go-containerregistry/pkg/name"
	"github.com/pkg/errors"
)

const (
	alpineTagRegex = "^.*-r[0-9]{1}$"
	// Limit # of goroutines because otherwise we hit "429 Too Many Requests" getting digests from DockerHub
	maxGoRoutines = 3
)

var (
	distrolessImage string
	dockerImageTag  string
	dockerImage     string
	excludedTags    string
)

func init() {
	flag.StringVar(&distrolessImage, "distroless-image", "", "Distroless image to tag")
	flag.StringVar(&dockerImageTag, "docker-image-tag", "", "Docker image tag to match against")
	flag.StringVar(&dockerImage, "docker-image", "", "Docker image to compare against")
	flag.StringVar(&excludedTags, "excluded-tags", "", "Comma separated list of tag regexes to ignore")
	flag.Parse()
}

func main() {
	if err := tag(); err != nil {
		fmt.Println(err)
		os.Exit(1)
	}
}

func tag() error {
	if dockerImageTag == "" {
		var err error
		dockerImageTag, err = getDockerImageTag()
		if err != nil {
			return errors.Wrap(err, "get docker image tag")
		}
		if dockerImageTag == "" {
			fmt.Println("Nothing to retag, skipping")
			return nil
		}
	}
	distrolessImageTagged := fmt.Sprintf("%s:%s", distrolessImage, dockerImageTag)
	if _, err := name.NewTag(distrolessImage); err == nil {
		distrolessImageTagged = distrolessImage
	}

	image := fmt.Sprintf("%s:%s", dockerImage, dockerImageTag)
	fmt.Fprintf(os.Stdout, "Getting digest for %s\n", image)

	dockerImageDigest, err := crane.Digest(image)
	if err != nil {
		return errors.Wrap(err, "digest")
	}

	at, err := additionalTags(dockerImageDigest)
	if err != nil {
		return errors.Wrap(err, "additional tags")
	}

	fmt.Println("Additional tags: ", at)
	for _, t := range at {
		fmt.Fprintf(os.Stdout, "Tagging %s with %s\n", distrolessImage, t)
		if err := crane.Tag(distrolessImageTagged, t); err != nil {
			return err
		}
	}
	return nil
}

func getDockerImageTag() (string, error) {
	latestDigest, err := crane.Digest(fmt.Sprintf("%s:%s", distrolessImage, "latest"))
	if err != nil {
		return "", errors.Wrap(err, "digest latest")
	}
	tags, err := crane.ListTags(distrolessImage)
	if err != nil {
		return "", errors.Wrap(err, "list tags")
	}
	regex, err := regexp.Compile(alpineTagRegex)
	if err != nil {
		return "", errors.Wrap(err, "compile regex")
	}
	for _, tag := range tags {
		if !regex.Match([]byte(tag)) {
			fmt.Println("Skipping", tag)
			continue
		}
		newImage := fmt.Sprintf("%s:%s", distrolessImage, tag)
		newDigest, err := crane.Digest(newImage)
		if err != nil {
			return "", err
		}
		if newDigest != latestDigest {
			fmt.Println(tag, "is not the latest digest, skipping")
			continue
		}
		newTag := strings.Split(tag, "-")[0]
		if err := crane.Tag(fmt.Sprintf("%s:%s", distrolessImage, tag), newTag); err != nil {
			return "", errors.Wrap(err, "tagging image")
		}
		return newTag, nil
	}
	return "", nil
}

func additionalTags(dockerImageDigest string) ([]string, error) {
	var at []string

	fmt.Fprintf(os.Stdout, "Looking for tags with matching digest %s\n", dockerImageDigest)

	// Get all tags for the docker image
	tags, err := crane.ListTags(dockerImage)
	if err != nil {
		return nil, errors.Wrap(err, "list tags")
	}

	var wg sync.WaitGroup
	wg.Add(len(tags))

	fmt.Fprintf(os.Stdout, "There are %d tags\n", len(tags))

	waitChan := make(chan struct{}, maxGoRoutines)
	excludedRegexs, err := excludedTagRegexps()
	if err != nil {
		return nil, errors.Wrap(err, "getting excluded regexes")
	}

	for _, t := range tags {
		waitChan <- struct{}{}
		go func(t string) {
			defer wg.Done()
			defer func() {
				<-waitChan
			}()
			if excludeAdditionalTag(t, excludedRegexs) {
				return
			}
			digest, err := crane.Digest(fmt.Sprintf("%s:%s", dockerImage, t))
			if err != nil {
				fmt.Fprintf(os.Stdout, "WARN: error getting digest, skipping: %v\n", err)
				return
			}
			if digest == dockerImageDigest {
				fmt.Fprintf(os.Stdout, "Found matching tag %s\n", t)
				at = append(at, t)
			}
		}(t)
	}

	wg.Wait()
	return at, nil
}

func excludeAdditionalTag(tag string, regexps []*regexp.Regexp) bool {
	for _, r := range regexps {
		if r.Match([]byte(tag)) {
			return true
		}
	}
	return false
}

func excludedTagRegexps() ([]*regexp.Regexp, error) {
	if excludedTags == "" {
		return nil, nil
	}
	var regexps []*regexp.Regexp
	sep := strings.Split(excludedTags, ",")
	for _, s := range sep {
		regex, err := regexp.Compile(s)
		if err != nil {
			return nil, errors.Wrapf(err, "compile regex %s", s)
		}
		regexps = append(regexps, regex)
	}
	return regexps, nil
}
