Limitations: 

Using data from Grad Cafe sites has limitations because the data is user submitted, anonymous, which means it has not gone through a strict data collecting process. The data quality is highly likely to be poor. Submitted data may not be clean, and some fields may be missing and the naming of the university may not be consistent. Further more, applicants with waitlisted or rejected status may have little or no motication to submit data, so that it causes bias in the data.  Since it is anonymous, it is impossible to verify or correct the mistakes. 

For example, when I calculate the percentage of international students for Fall 2026, the numbers only describe the people who submitted data to Grad Café, not all applicants. Another example is that when I calculate average GPAs, a lot of records do not have GPAs available (missing data). The results are not reliable. Analysis results from this data can provide some insight and trend, but can not be used for scientific study or offical records due to the quality of the data.   


------------------------------------------------------------------------------------
Explainations of each queries: 

Q1: "How many entries do you have in your database who have applied for Fall 2026?"

     "sql"= "SELECT count(*) FROM applicants where term = 'Fall 2026'"

    where is used to filter the term. Count is used to count number of rows. 

    Answer: 33052

   

Q2: "What percentage of entries are from international students (not American or Other) (to two decimal places)?",
        "sql"= """
            SELECT ROUND(
                100.0 * SUM(CASE WHEN us_or_international = 'International' THEN 1 ELSE 0 END) / COUNT(*),
                2
            ) AS international_pct
            FROM applicants;
        """,
    First it create binary 1/0, when it is international, the value is 1, else it is 0. The sum up all the 1s and divided by the total number-- count(*).
   
   Answer: [(Decimal('45.22'),)]

Q3: "What is the average GPA, GRE, GRE V, GRE AW of applicants who provide these metrics?",
      "sql"= """
            SELECT
                ROUND(AVG(gpa)::numeric, 2) AS avg_gpa,
                ROUND(AVG(gre)::numeric, 2) AS avg_gre,
                ROUND(AVG(gre_v)::numeric, 2) AS avg_gre_v,
                ROUND(AVG(gre_aw)::numeric, 2) AS avg_gre_aw
            FROM applicants;
        """,


    avg_gpa, avg_gre, avg_gre_v, avg_gre_aw = query3_output[0]

    print("Average GPA:", avg_gpa)
    print("Average GRE:", avg_gre)
    print("Average GRE V:", avg_gre_v)
    print("Average GRE AW:", avg_gre_aw)

    Take average of each corresponding vars and then round to 2 decimal points


    Answer: Average GPA: 3.78
    Average GRE: 262.00
    Average GRE V: 161.54
    Average GRE AW: 9.30

Q4: "What is their average GPA of American students in Fall 2026?",
        "sql"= """
            SELECT ROUND(AVG(gpa)::numeric, 2) AS avg_gpa
            FROM applicants
            WHERE us_or_international = 'American'
              AND term = 'Fall 2026';
        """,
Where clause put filter and table average and then round to 2 decimal points. 

Answer: [(Decimal('3.79'),)]

Q5: "What percent of entries for Fall 2026 are Acceptances (to two decimal places)?",
        "sql": """
         SELECT
            ROUND(
                100.0 * SUM(
                    CASE WHEN status ILIKE '%Accepted%' THEN 1
                        ELSE 0
                    END
                ) / COUNT(*),
                2
            ) AS fall_2026_accept_pct
        FROM applicants
        WHERE term = 'Fall 2026';
        """
    First where clause select the term. Case when status includes "Accepted" then create binary 1, 
    otherwise 0. Sum up all the 1s then divided by the total. 
    Times 100 and round to 2 decimal to get the rounded decimal. 

    Answer: [(Decimal('35.84'),)]

Q6: "What is the average GPA of applicants who applied for Fall 2026 who are Acceptances?",
        "sql": """
            SELECT
                 ROUND(AVG(gpa), 2)
            FROM applicants
            where term = 'Fall 2026' and status ILIKE '%Accepted%';
        """,
    
    Where clause filter the data in term and status. Then calculate average. Round to 2 decimal points. 
    
    Answer: 3.78
    
  Q7: "How many entries are from applicants who applied to JHU for a masters degrees in Computer Science?",
        "sql": """
           SELECT count(*)
           FROM applicants
           WHERE degree = 'Masters'
            AND (
                program ILIKE '%Johns Hopkins%'
                OR program ILIKE '%John Hopkins%'
                OR program ILIKE '%JHU%'
            )
            AND program ILIKE '%computer science%';
        """,
   
   Where clause finds records have Johns Hopkins or JHU or John Hopkins in program, and Masters in degree. 
   Count to count all the selected records. 
   
   Answer: 14
   
Q8: "How many entries from 2026 are acceptances from applicants who applied to Georgetown University, MIT, Stanford University, or Carnegie Mellon University for a PhD in Computer Science?",
        "sql": """
           SELECT COUNT(*)
            FROM applicants
            WHERE status = 'Accepted'
            AND degree = 'PhD'
            AND program ILIKE '%computer science%'
            AND EXTRACT(YEAR FROM date_added) = 2026
            AND (
                program ILIKE '%Georgetown%'
                OR program ILIKE '%Stanford%'
                OR program ILIKE '%Carnegie Mellon%'
                OR program ILIKE '%Massachusetts Institute of Technology%'
                OR program ILIKE '%MIT%'
            );
        """,

Where clause finds records status = 'Accepted' AND degree = 'PhD' and program includes the university names, 
Extract the year from date_added. 
Count to count all the selected records. 

Answer: 0


Q9: "Same as Q8, using LLM-generated program and university fields.",
        "sql": """
            SELECT COUNT(*) AS entries
            FROM applicants
            WHERE status ILIKE 'Accepted%'
              AND degree = 'PhD'
              AND llm_generated_program ILIKE '%computer science%'
              AND EXTRACT(YEAR FROM date_added) = 2026
              AND (
                  llm_generated_university ILIKE '%Georgetown%'
                  OR llm_generated_university ILIKE '%Stanford%'
                  OR llm_generated_university ILIKE '%Carnegie Mellon%'
                  OR llm_generated_university ILIKE '%Massachusetts Institute of Technology%'
                  OR llm_generated_university ILIKE '%MIT%'
              );
        """,
    Same as Question8, just use llm_generated_university and llm_generated_program instead of program. 

    Answer: 0

Q10: "How many entries for students applied for Fall 2026 term for Stanford Univerity Masters program per acceptance status? ",
        "sql": """
           SELECT
                CASE
                    WHEN status ILIKE 'Accepted%' THEN 'Accepted'
                    WHEN status ILIKE 'Rejected%' THEN 'Rejected'
                    WHEN status ILIKE 'Wait listed%' THEN 'Waitlisted'
                    WHEN status ILIKE 'Interview%' THEN 'Interview'
                    ELSE status
                END AS acceptance_status,
                COUNT(*) AS num_entries
            FROM applicants
            WHERE term = 'Fall 2026'
            AND degree = 'Masters'
            AND llm_generated_university ILIKE '%Stanford%'
            GROUP BY acceptance_status
            ORDER BY num_entries DESC;
        """,
    
    Where clause put filter on term, degree, llm_generated_university. Case when created categorical fields based on partial match. 
    Grouped by acceptance_status. Count entries per group. 

    Answer: [('Rejected', 68), ('Accepted', 49), ('Interview', 2), ('Waitlisted', 2)]

 
Q11: "For students applied for Fall 2026 term for Stanford Univerity Masters program and got accepted, what is the percentage of international student?",
        "sql": """
           SELECT
            ROUND(
                100.0 * SUM(
                    CASE WHEN us_or_international = 'International' THEN 1
                        ELSE 0
                    END
                ) / COUNT(*),
                2
            ) AS international_student_percent
        FROM applicants
        WHERE term = 'Fall 2026'
        AND degree = 'Masters'
        AND llm_generated_university ILIKE '%Stanford%'
        AND status ILIKE 'Accepted%';
        """,
 
Where clause put filter on term, degree, llm_generated_university and status. 
Case when created binary based on us_or_international. 
sum up international. 
divided by total
times 100, and round to 2 decimal points. 


 Answer: [(Decimal('38.78'),)]

