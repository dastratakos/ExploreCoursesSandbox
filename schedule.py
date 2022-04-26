"""
file: schedule.py
author: Dean Stratakos
date: April 26, 2022
----------------------
The MySchedule class represents a 4-year plan of classes. Each class has a
subject, code, description, and units_max.
"""

import json


class MySchedule:

    def __init__(self, filename, major=None, start_term=None):
        """Initializes a MySchedule object. Can read from a file or take in a
        major and start_term.

        Args:
            start_term (Term): The first term of the schedule
        """
        self.filename = filename

        self.major = major
        self.start_term = start_term

        self.schedule = {}

        self.num_years = 4

        self.MIN_UNITS_PER_TERM = 12
        self.MAX_UNITS_PER_TERM = 20

        if filename:
            with open(filename, "r") as f:
                data = json.load(f)
                self.major = data["major"]
                self.start_term = data["start_term"]
                self.schedule = data["schedule"]

    def save(self):
        """Updates persistent storage (i.e. the file).
        """
        data = {
            "major": self.major,
            "start_term": self.start_term,
            "schedule": self.schedule
        }
        with open(self.filename, "w") as f:
            json.dump(data, f)

    def add_course(self, course, term):
        """Adds a course to the schedule at the specified term. Updates the
        file.

        Args:
            course (Course): the Course object to add
            term (str): e.g. "2018-2019 Autumn"
        """
        quarters = []
        for attr in course.attributes:
            if attr.name == "NQTR":
                if attr.value == "AUT":
                    quarters.append("A")
                elif attr.value == "WIN":
                    quarters.append("W")
                elif attr.value == "SPR":
                    quarters.append("S")
                elif attr.value == "SUM":
                    quarters.append("s")

        course_obj = {
            "subject": course.subject,
            "code": course.code,
            "title": course.title,
            "units_max": course.units_max,
            "quarters": ",".join(quarters)
        }

        if term in self.schedule:
            self.schedule[term]["courses"].append(course_obj)
        else:
            self.schedule[term] = {"courses": [course_obj]}

        self.save()

    def remove_course(self, course, term):
        """Removes a course from the schedule at the specified term. Updates the 
        file.

        Args:
            course (Course): the Course object to remove
            term (str): e.g. "2018-2019 Autumn"
        """

        if term not in self.schedule:
            return

        for i in range(self.schedule[term]):
            if self.schedule[term][i].subject == course.subject and \
               self.schedule[term][i].code == course.code:
                self.schedule[term].pop(i)
                break

        self.save()

    def get_GERs_unsatisfied(self):
        """Returns a dictionary.

        {
            "WAYS": ["AII1", "AII2", "FR", etc.],
            "THINK": ["THINK"],
            "PWR": ["PWR1", "PWR2"]
        }

        """
        pass

    def is_complete(self):
        """Returns true if major requirements, GERs, language requirement, etc.
        are satisfied.
        """
        pass

    def is_valid(self):
        """Returns true if prereqs are valid, etc.
        """
        pass

    def __str__(self):
        """
        Returns a string representation of the Schedule
        """

        ret_str = ""

        # append major
        ret_str += f"Major: {self.major}\n"

        start_term_year, _ = self.start_term.split()
        start_term_year = int(start_term_year.split("-")[0])

        quarters = ["Autumn", "Winter", "Spring", "Summer"]

        COL_WIDTH = 21
        NUM_QUARTERS = 4
        NUM_COURSES_PER_QUARTER = 6

        for year in range(start_term_year, start_term_year + self.num_years):
            ret_str += "=" * ((COL_WIDTH + 1) * NUM_QUARTERS + 1) + "\n"

            for quarter in quarters:
                ret_str += f"|{quarter.center(COL_WIDTH)}"
            ret_str += "|\n"

            ret_str += f"|{'-' * COL_WIDTH}" * NUM_QUARTERS + "|\n"

            unit_totals = {quarter: 0 for quarter in quarters}

            for i in range(NUM_COURSES_PER_QUARTER):
                for quarter in quarters:
                    term = f"{year}-{year + 1} {quarter}"
                    id = ""
                    units = ""
                    if term in self.schedule and \
                       i < len(self.schedule[term]["courses"]):
                        course = self.schedule[term]["courses"][i]
                        id = f"{course['subject']} {course['code']}"
                        units = str(course["units_max"])
                        unit_totals[quarter] += course["units_max"]
                    ret_str += f"| {id.ljust(COL_WIDTH - 6)}| {units.rjust(2)} "
                ret_str += "|\n"

            ret_str += f"|{'-' * COL_WIDTH}" * NUM_QUARTERS + "|\n"

            for quarter in quarters:
                ret_str += f"| {'Total'.ljust(COL_WIDTH - 6)}" + \
                           f"| {str(unit_totals[quarter]).rjust(2)} "
            ret_str += "|\n"

        ret_str += "=" * ((COL_WIDTH + 1) * NUM_QUARTERS + 1)

        return ret_str


if __name__ == "__main__":
    schedule = MySchedule("dean_schedule.json")
    print(schedule)
