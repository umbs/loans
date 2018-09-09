            RESPONSES TO QUESTIONS
            ======================
Q: How long did you spend working on the problem? What did you find to be the
most difficult part?
A: Close to 4.5 hours. Nothing was particularly difficult, but 'subtle'
restrictions in Covenants took time to understand. For example, following two
from same bank 

    1,0.06,2,VT
    1,,2,CA

- I also had to read/look up many things along the way (did not list here, but
  copious amount of help from StackOverflow and Google). Some of them are
    * cvs module
    * cvs.reader vs cvs.DictReader. I probably should have used DictReader and
      DictWriter
    * How to ignore header rows after reading
    * Compound keys to dictionary. Best ways to construct them
    * Rounding up/down of floats using 'decimal' module
    * Create folders & files using 'os' module
    and few more minor stuff

Q: How would you modify your data model or code to account for an eventual
introduction of new, as-of-yet unknown types of covenants, beyond just maximum
default likelihood and state restrictions?
A: Few changes are needed:
    a. Currently the __init__ methods and other methods don't take variable
keyword arguments (*args, **kwargs). Modify code to do that.
    b. I put 'NOTE' in the code where changes are needed when additional
restrictions come in.


Q: How would you architect your solution as a production service wherein new
facilities can be introduced at arbitrary points in time. Assume these
facilities become available by the finance team emailing your team and
describing the addition with a new set of CSVs.
A:
    a. REST APIs to add, delete or update facilities that accepts new csv file
as input.
    b. API writes new facilities to Postgres (or DB of choice)
    c. There's a service periodically checking DB for updates to Facilities
table and accordingly updating it's in-memory cache of Facilities


Q: Your solution most likely simulates the streaming process by directly calling
a method in your code to process the loans inside of a for loop. What would a
REST API look like for this same service? Stakeholders using the API will need,
at a minimum, to be able to request a loan be assigned to a facility, and read
the funding status of a loan, as well as query the capacities remaining in
facilities.
A:

REST APIs: (Assume basepath is: www.domainname.com:port)
[1] Request a loan:
HTTP Request Type: GET
/loanprocessor/v1/loan?amount=XX?state=XX??ssn=XX
Query Params: amount, origination state, social security (for credit check)
Return Values: JSON output of Generated loan_id, loan status

Example:
{
"result": {"loan_id": 5, "loan_status": Pending}
}

{
"result": {"loan_id": 9, "loan_status": Accepted}
}


[2] Status of a loan:
HTTP Request Type: GET
/loanprocessor/v1/loan/status?loan_id=XX
Query Params: loan_id
Return Values: JSON output of loan status
{
"result": {"loan_id": 9, "loan_status": Accepted, "Bank": "Bank Name"}
}


[3] Facility capacity:
HTTP Request Type: GET
/loanprocessor/v1/facility/status?facility_id=XX?bank_id=XX
Query Params: Provide facility_id and bank_id of that facility
Return Values:

{
"result":
    {"facility_id": 2,
     "bank_name": "Bank Name",
     "amount": 65034,
     "expected_yield": 5404,
    }
}


Q: How might you improve your assignment algorithm if you were permitted to
assign loans in batch rather than streaming? We are not looking for code here,
but pseudo code or description of a revised algorithm appreciated.
A: The problem will then have similarities to fields in Supply Chain Management,
or Process/Task scheduling. If more time is present, I'll research for existing
algorithms. However, my first approach would be this

Algorithm/Pseudo Code
===
- Use Greedy approach in assigning loans to facilities

- Have facilities sorted in increasing order of interest rates
- Have loans in the batch sorted in increasing order of default likelihood

- Subject to availability of funds and covenants, assign as many loans as
  possibile to each facility before looking for next facility

Q: Discuss your solution’s runtime complexity.
A:

Time Complexity
===
- If there are F facilities, running time is O(F) for EACH loan
- If there are N loans, running time is O(NF)

For each loan, we do following
    1. Look up list of facilities
    2.   For a given facility, look up it's covenants
    3.     Check if covenants pass
    4.     if passes, assign the loan
    5.     else, continue looking for next facility
    6. A loan is served (or not) by a facility

- Line 2-6 run in constant time, as I have used dictionary to maintain
  Covenants. The pass/fail check on covenant is constant time.
- Line 1 iterates over (potentially) all facilities.
- So, for N loans, running time of algorithm is: O(NF)

Space Complexity
===
- I maintain all resources in memory. So, there's a "linear" proportion of
  space consumed
F: # of facilities
N: # of loans
C: # of covenants
B: # of banks

- Space consumed is: O(F+N+C+B)
 
