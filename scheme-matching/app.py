from flask import Flask, render_template, request
import json

app = Flask(__name__)


# =========================================================
# LOAD SCHEME DATA
# =========================================================

with open("data/schemes.json", "r", encoding="utf-8") as file:
    schemes = json.load(file)


# =========================================================
# SCHEME MATCHING ENGINE
# =========================================================

def calculate_match(
    scheme,
    purpose,
    project_cost,
    income,
    education
):

    score = 0
    reasons = []

    # -----------------------------------------------------
    # 1. INCOME ELIGIBILITY
    # -----------------------------------------------------

    income_limit = scheme.get("income_limit")

    # If the scheme has an income limit, check it.
    # If income_limit is null, treat it as "no specified limit".
    if income_limit is not None:

        if income <= float(income_limit):

            score += 30

            reasons.append(
                "Family income is within the eligibility limit"
            )

        else:

            return 0, [
                "Family income exceeds the eligibility limit"
            ]

    else:

        score += 30

        reasons.append(
            "No specific income limit is specified for this scheme"
        )


    # -----------------------------------------------------
    # 2. EDUCATION / BUSINESS MATCH
    # -----------------------------------------------------

    if scheme.get("category") in ["education", "education_abroad"]:

        if education == "yes":

            score += 30

            reasons.append(
                "Education requirement matches"
            )

        else:

            return 0, [
                "This scheme is intended for education"
            ]

    else:

        if education == "no":

            score += 10

            reasons.append(
                "Business funding requirement matches"
            )


    # -----------------------------------------------------
    # 3. PROJECT COST
    # -----------------------------------------------------

    project_cost_max = scheme.get("project_cost_max")

    # Only check project cost when the scheme specifies a limit
    if project_cost_max is not None:

        if project_cost <= float(project_cost_max):

            score += 30

            reasons.append(
                "Project cost is within the scheme limit"
            )

        else:

            return 0, [
                "Project cost exceeds the scheme limit"
            ]

    else:

        # Scholarship/fellowship/grant schemes may not
        # have a project-cost limit.
        score += 30

        reasons.append(
            "No specific project cost limit is specified"
        )


    # -----------------------------------------------------
    # 4. PURPOSE MATCH
    # -----------------------------------------------------

    purpose_lower = purpose.lower()

    for allowed_purpose in scheme.get("purposes", []):

        allowed_lower = allowed_purpose.lower()

        if (
            allowed_lower in purpose_lower
            or purpose_lower in allowed_lower
        ):

            score += 10

            reasons.append(
                "Funding purpose matches the scheme"
            )

            break


    return min(score, 100), reasons

# =========================================================
# HOME PAGE
# =========================================================

@app.route("/")
def home():

    return render_template(
        "index.html"
    )


# =========================================================
# SCHEME MATCHER
# =========================================================

@app.route(
    "/matcher",
    methods=["GET", "POST"]
)
def matcher():

    if request.method == "POST":

        purpose = request.form.get(
            "purpose",
            ""
        )

        project_cost = float(
            request.form.get(
                "project_cost",
                0
            )
        )

        income = float(
            request.form.get(
                "income",
                0
            )
        )

        education = request.form.get(
            "education",
            ""
        )


        results = []


        # Check every scheme

        for scheme in schemes:

            score, reasons = calculate_match(
                scheme,
                purpose,
                project_cost,
                income,
                education
            )


            if score > 0:

                results.append({

                    "scheme": scheme,

                    "score": score,

                    "reasons": reasons

                })


        # Highest match first

        results.sort(
            key=lambda x: x["score"],
            reverse=True
        )


        return render_template(
            "matcher.html",
            results=results,
            submitted=True
        )


    # GET request

    return render_template(
        "matcher.html",
        results=[],
        submitted=False
    )


# =========================================================
# EMI CALCULATOR
# =========================================================

@app.route("/emi/<scheme_id>")
def emi(scheme_id):
    scheme = next(
        (
            s
            for s in schemes
            if s["id"] == scheme_id
        ),
        None
    )

    if scheme is None:
        return "Scheme not found", 404

    project_cost = request.args.get(
        "project_cost",
        ""
    )

    return render_template(
        "emi.html",
        scheme=scheme,
        project_cost=project_cost
    )
# =========================================================
# NEARBY PARTNERS
# =========================================================

@app.route(
    "/partners/<scheme_id>"
)
def partners(scheme_id):

    scheme = next(
        (
            s
            for s in schemes
            if s["id"] == scheme_id
        ),
        None
    )


    if scheme is None:

        return (
            "Scheme not found",
            404
        )


    # -----------------------------------------------------
    # DEMO PARTNER DATA
    # -----------------------------------------------------
    #
    # These are prototype locations only.
    # A production version would obtain partner information
    # from authenticated government/channel-partner data.
    # -----------------------------------------------------

    partner_data = [

        {
            "name": "State Channelizing Agency",

            "type": "SCA",

            "city": "Kolkata",

            "distance": "2.4 km",

            "status": "Accepting Applications",

            "latitude": 22.5726,

            "longitude": 88.3639
        },


        {
            "name": "Regional Rural Bank",

            "type": "RRB",

            "city": "Kolkata",

            "distance": "4.1 km",

            "status": "Accepting Applications",

            "latitude": 22.5958,

            "longitude": 88.2636
        },


        {
            "name": "Public Sector Bank",

            "type": "PSB",

            "city": "Kolkata",

            "distance": "5.7 km",

            "status": "Limited Capacity",

            "latitude": 22.5200,

            "longitude": 88.3500
        }

    ]


    return render_template(
        "partners.html",
        scheme=scheme,
        partners=partner_data
    )


# =========================================================
# RUN APPLICATION
# =========================================================

if __name__ == "__main__":

    app.run(
        debug=True
    )