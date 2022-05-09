import json
import os
from pprint import pprint
import random
import time
import xml.etree.ElementTree as ET

from explorecourses import *
from explorecourses import filters

from schedule import MySchedule


def get_courses_by_query_raw(query: str, *filters: str, year=None):
    """ Downloads the courses matching the query using the API from the
    explorecourses module.

    Args:
        query (str):           The query of the call.
        year (int, optional):  The year to query. Defaults to None.

    Returns:
        bytes:                 An XML object containing all the courses.
    """
    connect = CourseConnection()

    url = connect._URL + "search"

    payload = {
        "view": "xml-20200810",
        "filter-coursestatus-Active": "on",
        "q": query,
    }
    payload.update({f: "on" for f in filters})
    if year:
        payload.update({"academicYear": year.replace('-', '')})

    res = connect._session.get(url, params=payload)

    return res.content


def download_courses_from_connection(school: str, code: str, *filters: str,
                                     year: int = None, dir: str = "data"):
    """ Downloads the courses from a specific school and department for a given
    year using get_courses_by_query_raw(). The data is then saved as .xml files
    to the specified dir.

    Args:
        school (str):          The school to query.
        code (str):            The department to query.
        year (int, optional):  The year to query. Defaults to None.
        dir (str, optional):   The directory to write files to after they are
                               downloaded. Defaults to "data".

    Returns:
        bytes:                 An XML object containing all the courses.
    """
    filters = list(filters)
    filters.append(f"filter-departmentcode-{code}")

    courses = get_courses_by_query_raw(code, *filters, year=year)

    if not os.path.exists(f"{dir}"):
        os.mkdir(f"{dir}")

    if not os.path.exists(f"{dir}/{school}"):
        os.mkdir(f"{dir}/{school}")

    if not os.path.exists(f"{dir}/{school}/{code}.xml"):
        with open(f"{dir}/{school}/{code}.xml", "xb") as f:
            f.write(courses)

    return courses


def get_all_courses_from_downloads(dir: str = "data"):
    print("Getting all courses from downloads...")

    total_start = time.time()

    all_courses = []

    for school in sorted(os.listdir(dir)):
        if os.path.isfile(os.path.join(dir, school)):
            continue

        start = time.time()

        departments = sorted(os.listdir(os.path.join(dir, school)))

        for dept in departments:
            with open(f"{dir}/{school}/{dept}") as f:
                root = ET.fromstring(f.read())
                courses = root.findall(".//course")
                all_courses.extend([Course(course) for course in courses])

        end = time.time()
        print(f"({end - start:.2f} s) {school}: {len(departments)}")

    total_end = time.time()
    print(f"Total time: {total_end - total_start:.2f} s")
    print(f"Total courses: {len(all_courses)}\n")

    return all_courses


def get_all_courses_from_connection():
    """ Gets all ExploreCourses courses using the API from the explorecourses
    module.

    Returns:
        List:  A list of all the courses (length around 9-10 thousand).
    """
    print("Getting all courses from connection...")

    total_start = time.time()

    connect = CourseConnection()

    # filter for actively offered courses
    filters_list = {
        filters.AUTUMN,
        filters.WINTER,
        filters.SPRING,
        filters.SUMMER
    }

    # Get all courses for 2021-2022
    all_courses = []
    year = "2021-2022"
    for school in connect.get_schools(year):
        start = time.time()

        for dept in school.departments:
            courses = connect.get_courses_by_department(
                dept.code, *filters_list, year=year)
            all_courses.extend(courses)

        end = time.time()
        print(f"({end - start:.2f} s) {school}: {len(school.departments)}")

    total_end = time.time()
    print(f"Total time: {total_end - total_start:.2f} s")
    print(f"Total courses: {len(all_courses)}\n")

    return all_courses


def download_all_courses(dir: str = "data"):
    """ Downloads all active courses from ExploreCourses and saves the data to
    the specified directory.

    Args:
        dir (str, optional):  The directory to save data to. Defaults to "data".
    """
    print("Downloading all courses...")

    total_start = time.time()

    connect = CourseConnection()

    # filter for actively offered courses
    filters_list = {
        filters.AUTUMN,
        filters.WINTER,
        filters.SPRING,
        filters.SUMMER
    }

    # Get all courses for 2021-2022
    all_courses = []
    year = "2021-2022"
    for school in connect.get_schools(year):
        start = time.time()

        for dept in school.departments:
            courses = download_courses_from_connection(
                school, dept.code, *filters_list, year=year, dir=dir)
            all_courses.extend(courses)

        end = time.time()
        print(f"({end - start:.2f} s) {school}: {len(school.departments)}")

    total_end = time.time()
    print(f"Total time: {total_end - total_start:.2f} s")
    print(f"Total courses: {len(all_courses)}\n")


def create_schedule(all_courses):
    """ Generates a random schedule and saves the result to the file
    schedules/my_schedule.json. Each quarter, the unit count is at least 15
    units.

    Args:
        all_courses (List):  A list of courses to choose from.
    """

    def reset_file(filename):
        """ Resets the given file using the blank_schedule template.

        Args:
            filename (str):  The name of the file to reset.
        """
        with open("schedules/blank_schedule.json", "r") as dummy:
            data = json.load(dummy)
            with open(filename, "w") as f:
                json.dump(data, f)

    reset_file("schedules/my_schedule.json")
    schedule = MySchedule("schedules/my_schedule.json")
    print(schedule)

    # fill schedule out with random courses
    quarters = ["Autumn", "Winter", "Spring"]
    for year in range(2018, 2022):
        for quarter in quarters:
            term = f"{year}-{year + 1} {quarter}"

            current_unit_count = 0
            while current_unit_count <= 15:

                # choose the course
                course = None
                found_course = False
                while not found_course:
                    course = random.choice(all_courses)
                    for attr in course.attributes:
                        if attr.name == "NQTR" and attr.description == quarter:
                            found_course = True
                            break

                current_unit_count += course.units_max
                schedule.add_course(course, term)

    print(schedule)


def count_sections_and_schedules(all_courses):
    """ Counts the number of Sections in each Course object and the number of
    Schedules in each Section object.

    Args:
        all_courses (List):  The list of all courses to count.
    """
    section_lengths = {}
    sched_lengths = {}

    for course in all_courses:
        num_sections = len(course.sections)
        section_lengths[num_sections] = section_lengths.get(
            num_sections, 0) + 1

        for section in course.sections:
            num_scheds = len(section.schedules)
            sched_lengths[num_scheds] = sched_lengths.get(num_scheds, 0) + 1

    print("Section lengths:")
    pprint(section_lengths)
    print("Schedule lengths:")
    pprint(sched_lengths)


def download_cs_courses(dir: str = "data"):
    filters_set = {
        filters.AUTUMN,
        filters.WINTER,
        filters.SPRING,
        filters.SUMMER
    }
    filters_list = list(filters_set)
    filters_list.append(f"filter-departmentcode-CS")

    if not os.path.exists(f"{dir}"):
        os.mkdir(f"{dir}")

    if not os.path.exists(f"{dir}/CS"):
        os.mkdir(f"{dir}/CS")

    for i in range(1992, 2002):
        year = f"{i}-{i + 1}"
        print(year)
        courses = get_courses_by_query_raw("CS", *filters_list, year=year)

        with open(f"{dir}/CS/CS_{year}.xml", "xb") as f:
            f.write(courses)


def analyze_primary_schedules(all_courses):

    for course in all_courses:
        aut_count = {}
        win_count = {}
        spr_count = {}
        sum_count = {}

        for section in course.sections:
            # TODO: we would like to skip courses that are closed
            # if section.enrollStatus == "Closed":
            #     continue
            
            term = section.term.split()[-1]
            component = section.component

            if term == "Autumn":
                aut_count[component] = aut_count.get(component, 0) + 1
            elif term == "Winter":
                win_count[component] = win_count.get(component, 0) + 1
            elif term == "Spring":
                spr_count[component] = spr_count.get(component, 0) + 1
            elif term == "Summer":
                sum_count[component] = sum_count.get(component, 0) + 1

        for quarter, dict in [("Aut", aut_count), ("Win", win_count), ("Spr", spr_count), ("Sum", sum_count)]:
            unique_comp = ""
            for comp, count in dict.items():
                if count != 1:
                    continue
                if unique_comp == "" or unique_comp == "DIS":
                    unique_comp = comp
                    continue
                elif comp == "DIS":
                    continue
                
                print(f"{course.subject} {course.code} {quarter} ", end="")
                print(f"Multiple unique comps: {unique_comp}, {comp}")
                break


if __name__ == "__main__":
    # Call this method once to save all the courses locally
    # download_all_courses()

    # all_courses = get_all_courses_from_connection()
    all_courses = get_all_courses_from_downloads()

    # create_schedule(all_courses)
    # count_sections_and_schedules(all_courses)
    analyze_primary_schedules(all_courses)

    # download_cs_courses()
