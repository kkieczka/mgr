import sys

# This script tries to determine a list of libraries used by an app based on a
# list of imports made by it in the form of __sorted__ new-line- or space-separated
# list of package names (or, generally, anything which can be put after
# "import" statement in java).
# The algorithm to obtain a list of unique libraries is quite simple.
# It iterates over package names and calculates a distance between current and
# previous package name. The distance is simply a number of package name
# segments identical in both package names, counting from the beginning.
# If the distance is less than 2 (i.e. package names differ already on second
# segment) the current package name is assumed to belong to different library
# and is printed.

# calculates similarity as a number of package name segments
# equal in both package names, counting from beginning
def calculate_similarity(a, b):
    sim = 0
    for i in range(0, min(len(a), len(b))):
        if a[i] == b[i]:
            sim += 1
        else:
            break

    return sim


# takes string which is a sorted list of imported classes
def process(imports_str):
    imports_list = imports_str.replace("\n", " ").split(" ")

    print "Read %d entries" % len(imports_list)
    imports_list = [x.split(".") for x in imports_list]

    if len(imports_list) < 2:
        return

    current_a = imports_list[0]
    last_similarity = len(current_a)

    for i in range(1, len(imports_list)):
        current_b = imports_list[i]
        similarity = calculate_similarity(current_a, current_b)

        if similarity < 2:
            # current_b represents next library
            print ".".join(current_a[:last_similarity])
            last_similarity = len(current_b)
        else:
            last_similarity = similarity

        current_a = current_b


def main():
    input_str = sys.stdin.read()
    process(input_str)

if __name__ == "__main__":
    main()

