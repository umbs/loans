import csv
import sys
import os
import errno

from decimal import Decimal, ROUND_HALF_UP


class Facilities:
    """
    Maintains info about each debt facility
    """
    def __init__(self, amount=0, interest_rate=0.0, facility_id=0, bank_id=0,
                 expected_yield=0.0):
        self.amount = amount
        self.interest_rate = interest_rate
        self.facility_id = facility_id
        self.bank_id = bank_id
        self.expected_yield = expected_yield


class Bank:
    """
    Maintains info about a bank
    """
    def __init__(self, bank_id=0, bank_name=""):
        self.bank_id = bank_id
        self.bank_name = bank_name


class Covenants:
    """
    Restrictions set by banks per facility (or for all facilities of that bank)
    """
    def __init__(self, facility_id=0, max_default_hood=1.0, bank_id=0,
                 banned_state=""):
        self.bank_id = bank_id
        self.facility_id = facility_id  # Optional
        self.max_default_hood = max_default_hood
        self.banned_state = list()
        if banned_state:
            self.banned_state.append(banned_state)


class Loans:
    """
    Each loan request is captured by one object of this class
    """
    def __init__(self, interest_rate=0.0, amount=0, loan_id=0,
                 default_hood=0.0, state="", facility_id=0):
        self.loan_id = loan_id
        self.amount = amount
        self.interest_rate = interest_rate
        self.default_hood = default_hood
        self.state = state
        self.facility_id = facility_id


class LoanBooks:
    """
    Main class processing the loans, assinging to facilities and computing
    expected yields for each facility
    """
    def __init__(self):
        self.facilities = list()
        self.banks = list()
        self.covenants = dict()
        self.loans = list()

    def build_banks(self, banks_file):
        """
        Builds a list of banks from input file
        """

        if banks_file is None:
            print "Input banks file is None\n"
            return

        with open(banks_file, 'rb') as f:
            try:
                reader = csv.reader(f)

                # Skip the headers
                next(reader, None)

                for line in reader:
                    bank_id = int(line[0])
                    bank_name = str(line[1])
                    self.banks.append(Bank(bank_id, bank_name))
            except csv.Error as e:
                sys.exit('file %s, line %d: %s' % (banks_file,
                         reader.line_num, e))

    def print_banks(self):
        for b in self.banks:
            print b.bank_id, b.bank_name

    def build_facilities(self, facilities_file):
        """
        Builds a list of facilities from input file. The list is sorted based
        on interest rate (lowest rate at the start).
        """
        if facilities_file is None:
            print "Input facilities file is None\n"
            return

        with open(facilities_file, 'rb') as f:
            try:
                reader = csv.reader(f)

                # Skip the headers
                next(reader, None)

                for line in reader:
                    # NOTE: 'amount' in facilities file is in float
                    amount = int(float(line[0]))
                    interest_rate = float(line[1])
                    facility_id = int(line[2])
                    bank_id = int(line[3])
                    self.facilities.append(Facilities(amount, interest_rate,
                                           facility_id, bank_id))
            except csv.Error as e:
                sys.exit('file %s, line %d: %s' % (facilities_file,
                         reader.line_num, e))

        # Sort list in increasing interest rate
        self.facilities.sort(key=lambda x: x.interest_rate)

    def print_facilities(self):
        print "amt, int_rate, id, bank_id, yield"
        for f in self.facilities:
            print f.amount, f.interest_rate, f.facility_id, f.bank_id,\
                    f.expected_yield

    def build_loans(self, loans_file):
        """
        Builds a list of loans from input file.
        """
        if loans_file is None:
            print "Input loans file is None\n"
            return

        with open(loans_file, 'rb') as f:
            try:
                reader = csv.reader(f)

                # Skip the headers
                next(reader, None)

                for line in reader:
                    interest_rate = float(line[0])
                    amount = int(line[1])
                    loan_id = int(line[2])
                    default_hood = float(line[3])
                    state = str(line[4])
                    self.loans.append(Loans(interest_rate, amount, loan_id,
                                      default_hood, state))
            except csv.Error as e:
                sys.exit('file %s, line %d: %s' % (loans_file,
                         reader.line_num, e))

    def print_loans(self):
        print "int_rate, amt, id, default_rate, state, fac_id"
        for l in self.loans:
            print l.interest_rate, l.amount, l.loan_id, l.default_hood,\
                    l.state, l.facility_id

    def build_covenants(self, covenants_file):
        """
        Builds a list of covenants from input file. Chosen a dict() for this
        becausd, for a given facility, we need a quick lookup of related
        covenant
        """
        if covenants_file is None:
            print "Input covenants file is None\n"
            return

        with open(covenants_file, 'rb') as f:
            try:
                reader = csv.reader(f)

                # Skip the headers
                next(reader, None)

                for line in reader:
                    # treating None as zero. Facility id is optional
                    if line[0] is None:
                        line[0] = 0
                    facility_id = int(line[0])

                    # Strangely, max_default_likelihood is also optional as one
                    # of the input data shows
                    if line[1]:
                        max_default_hood = float(line[1])
                    else:
                        max_default_hood = 1.0
                    bank_id = int(line[2])
                    banned_state = str(line[3])

                    # NOTE: If any additional restrictions, they must be parsed
                    # and passed to class

                    fac = Covenants(facility_id, max_default_hood, bank_id,
                                    banned_state)

                    key = (fac.bank_id, fac.facility_id)

                    # There can be multiple banned states per bank
                    if key in self.covenants:
                        self.covenants[key].banned_state.append(banned_state)
                    else:
                        self.covenants[key] = fac

            except csv.Error as e:
                sys.exit('file %s, line %d: %s' % (covenants_file,
                         reader.line_num, e))

    def print_covenants(self):
        print "(bank_id, fac_id), max_default_rate, banned_states"
        for k, v in self.covenants.iteritems():
            print k, v.max_default_hood, v.banned_state

    def pass_covenant(self, cov, loan):
        """
        Does 'loan' passes or fails a 'covenant'
        """
        if loan.default_hood > cov.max_default_hood:
            return False
        if loan.state in cov.banned_state:
            return False
        # NOTE: Additional restrictions go here

        return True

    def get_facility(self, loan):
        """
        Given a loan, get the 'best' facility. How is 'best' computed?
            Search facilities for:
                a. lowest interest rate
                b. has sufficient funds to process loan
                c. loan origination state is not in banned list
        OPTIMIZE: The search through facilities list can be binary
        """
        for f in self.facilities:
            if f.amount < loan.amount:
                continue
            cov = self.covenants[(f.bank_id, f.facility_id)]
            if cov is None:
                # Check if covenant present at bank level
                cov = self.covenants[(f.bank_id, 0)]
                if cov is None:
                    # Perhaps this is possible. Some banks may not have any
                    # covenants
                    print "No covenant for bank: %d" % (f.bank_id)

            if cov and not self.pass_covenant(cov, loan):
                continue

            gains = (1-loan.default_hood) * loan.interest_rate * loan.amount
            default_cost = loan.default_hood * loan.amount
            facility_cost = f.interest_rate * loan.amount

            expected_yield = gains - default_cost - facility_cost

            return f, expected_yield

        return None, 0

    def serve_loans(self):
        """
        Go over list of loans and assign them to facilities, if possible
        """
        for l in self.loans:
            f, expected_yield = self.get_facility(l)
            if f is None:
                print "loan_id: %d cannot be served" % l.loan_id
                continue

            l.facility_id = f.facility_id
            f.expected_yield += expected_yield
            f.amount -= l.amount

    def write_loan_assignments(self, assignments_file):
        """
        Utility function to write output to file
        OPTIMIZE: Perhaps both write utilities can be combined in to one
        """
        if not os.path.exists(os.path.dirname(assignments_file)):
            try:
                os.makedirs(os.path.dirname(assignments_file))
            except OSError as e:
                if e.errno != errno.EEXIST:
                    raise

        with open(assignments_file, 'wb') as f:
            writer = csv.writer(f)
            writer.writerow(['loan_id', 'facility_id'])

            for l in self.loans:
                writer.writerow([l.loan_id, l.facility_id])

    def write_facility_yields(self, yields_file):
        """
        Utility function to write output to file
        """
        if not os.path.exists(os.path.dirname(yields_file)):
            try:
                os.makedirs(os.path.dirname(yields_file))
            except OSError as e:
                if e.errno != errno.EEXIST:
                    raise

        with open(yields_file, 'wb') as f:
            writer = csv.writer(f)
            writer.writerow(['facility_id', 'expected_yield'])

            for fac in self.facilities:
                writer.writerow([fac.facility_id, Decimal(fac.expected_yield).quantize(0, ROUND_HALF_UP)])

    def print_loan_status(self):
        print "id, Amt, Fid"
        for l in self.loans:
            print l.loan_id, l.amount, l.facility_id

    def print_facility_status(self):
        print "Fid, expt_yield, amnt_left"
        for f in self.facilities:
            print f.facility_id, f.expected_yield, f.amount


if __name__ == "__main__":
    """
    banks_infile = 'small/banks.csv'
    facilities_infile = 'small/facilities.csv'
    covenants_infile = 'small/covenants.csv'
    loans_infile = 'small/loans.csv'
    """

    banks_infile = 'large/banks.csv'
    facilities_infile = 'large/facilities.csv'
    covenants_infile = 'large/covenants.csv'
    loans_infile = 'large/loans.csv'

    assignments_outfile = 'output/assignments.csv'
    yields_outfile = 'output/yields.csv'

    loan_books = LoanBooks()
    loan_books.build_banks(banks_infile)
    loan_books.build_facilities(facilities_infile)
    # loan_books.print_facilities()
    loan_books.build_covenants(covenants_infile)
    loan_books.build_loans(loans_infile)

    loan_books.serve_loans()

    loan_books.write_loan_assignments(assignments_outfile)
    loan_books.write_facility_yields(yields_outfile)

    # loan_books.print_facilities()
