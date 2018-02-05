import sys
import os
import glob
import re
import fnmatch

main_build_gradle_patch = """

// PITest support
buildscript {
    repositories {
        mavenLocal()
    }
    dependencies {
        classpath 'pl.droidsonroids.gradle:gradle-pitest-plugin:%s'
    }
}
"""

module_build_gradle_patch = """

// PITest support
apply plugin: 'pl.droidsonroids.pitest'
pitest {
    pitestVersion = "2.2.1337"
    targetClasses = ['%s.*']
    targetTests = ['%s.*']
    mutators = ['EXPERIMENTAL_ALWAYS_TRUE_HOSTNAME_VERIFIER',
                'EXPERIMENTAL_ALWAYS_TRUSTING_TRUST_MANAGER',
                'EXPERIMENTAL_VULNERABLE_SSL_CONTEXT_PROTOCOL',
                'EXPERIMENTAL_HTTPS_TO_HTTP']
}
"""


def find_package_name(path):

    found_files = []
    for root, dirnames, filenames in os.walk(path):
        for filename in fnmatch.filter(filenames, "AndroidManifest.xml"):
            found_files.append(os.path.join(root, filename))

    if len(found_files) == 0:
        print "[-] find_package_name: Unable to find AndroidManifest.xml"
        return None

    if len(found_files) > 1:
        print "[!] find_package_name: More than one AndroidManifest.xml"

    # try every AndroidManifest.xml found, except these, which path contains '/build/'.
    # Such manifests usually contain applicationId instead of 'real' packageId.
    for manifest in found_files:
        if "/build/" in manifest:
            continue

        # read AndroidManifest.xml and find package name
        with open(manifest, "r") as f:
            xml = f.read()
            result = re.search("package=\"(\S+)\"", xml)
            if result:
                package_name = result.group(1)
                print "[*] find_package_name: Found package name: %s" % package_name
                return package_name
            else:
                print "[-] find_package_name: Couldn't find package name in %s" % manifest

    print "[-] find_package_name: Couldn't find package name in any of manifest files"
    return None


def make_file_copy(file_path):

    copy_path = file_path + ".cpy"

    if os.path.exists(file_path):
        if not os.path.exists(copy_path):
            os.rename(file_path, copy_path)
        else:
            print "[*] make_file_copy: %s already exists" % copy_path
            return copy_path
    else:
        print "[-] make_file_copy: %s does not exist" % file_path
        return None

    return copy_path


def do_patch(root_dir):
    print "[*] Root dir: %s" % root_dir
    everything_succeeded = True

    package_name = find_package_name(root_dir)
    if not package_name:
        print "[-] Unable to get package name, exiting"
        return 2

    # 1. Modify root build.gradle file

    build_gradle_path = os.path.join(root_dir, "build.gradle")
    build_gradle_cpy_path = make_file_copy(build_gradle_path)
    if not build_gradle_cpy_path:
        print "[-] Unable to do a file copy, exiting"
        return 2

    build_gradle = open(build_gradle_cpy_path, "r")
    buildscript = build_gradle.read()
    build_gradle.close()

    # determine PITest plugin version needed. Find 'com.android.tools.build:gradle:x.x.x'
    # If the version is 3.x.x or above, use plugin version 0.1.4, otherwise choose version
    # 0.0.11
    gradle_plugin_version = "0.0.11"
    gradle_dependency = re.search("com.android.tools.build:gradle:([0-9])", buildscript)
    if gradle_dependency:
        if gradle_dependency.group(1) == "3":
            gradle_plugin_version = "0.1.4"
        elif gradle_dependency.group(1) != "2":
            print "[!] Unknown main version of gradle: %s" % gradle_dependency.group(1)
            everything_succeeded = False
    else:
        print "[!] Unable to determine gradle version"
        everything_succeeded = False

    print "[*] Using gradle plugin version %s" % gradle_plugin_version

    # add additional repository mavenLocal() and gradle plugin dependency
    buildscript += main_build_gradle_patch % gradle_plugin_version

    # check if android {} block is present in file. If it is, than there is
    # a big chance that it is old-style build.gradle structure with everything
    # in one file. In such case, add also the patch as for module build.gradle files
    if re.search("android[\s]+{", buildscript):
        print "[*] Found android {} block in root build.gradle; appending module patch"
        buildscript += module_build_gradle_patch % (package_name, package_name)

    print "[+] Patching root build.gradle (%s)" % build_gradle_path
    new_build_gradle = open(build_gradle_path, "w")
    new_build_gradle.write(buildscript)
    new_build_gradle.close()

    # 2. Find build.gradle files in modules and append PITest config to them

    for module_build_gradle in glob.glob(os.path.join(root_dir, "*/build.gradle")):
        print "[*] Found module script: %s" % module_build_gradle
        copy = make_file_copy(module_build_gradle)
        if copy:
            build_gradle = open(copy, "r")
            buildscript = build_gradle.read()
            build_gradle.close()

            # add PITest config
            buildscript += module_build_gradle_patch % (package_name, package_name)

            print "[+] Patching module build.gradle (%s)" % module_build_gradle
            new_build_gradle = open(module_build_gradle, "w")
            new_build_gradle.write(buildscript)
            new_build_gradle.close()
        else:
            print "[!] Unable to do a file copy, skipping!"
            everything_succeeded = False

    if everything_succeeded:
        print "[+] All done"
        return 0
    else:
        print "[+] Finished, but some tasks failed"
        return 1


if __name__ == '__main__':
    res = 0
    if len(sys.argv) > 1:
        res = do_patch(sys.argv[1])
    else:
        res = do_patch(os.getcwd())

    sys.exit(res)
