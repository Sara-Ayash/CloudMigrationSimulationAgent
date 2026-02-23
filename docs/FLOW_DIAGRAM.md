# דיאגרמת זרימה – Cloud Migration Simulation

## זרימת ה-Agent (גרף אחד)

גרף זה מתאר את כל הצעדים שהמערכת (Agent) מבצעת מרגע קבלת הודעה מהמשתמש ועד החזרת תגובה.

```mermaid
flowchart TD
    START([הודעת משתמש נכנסת]) --> A[שמירת הודעה ב-State]
    A --> B[round_count += 1]
    B --> C{סבב סיום?<br/>in_final_review}
    C -->|כן| D[Parser: חילוץ אסטרטגיה + אילוצים]
    D --> E[עדכון State]
    E --> F[הערכה: evaluate_session]
    F --> G[format_feedback]
    G --> END1([החזרת פידבק סופי + סיום])
    C -->|לא| H[Parser: חילוץ אסטרטגיה + אילוצים]
    H --> I[עדכון State]
    I --> J{תנאי סיום<br/>מתקיימים?}
    J -->|כן| K[in_final_review = True]
    K --> L[format_final_review_message]
    L --> END2([החזרת הודעת סיכום ביניים])
    J -->|לא| M[בחירת דמות: choose_next_persona]
    M --> N[PM / DevOps / CTO]
    N --> O[generate_complication]
    O --> Q[persona.respond_as_persona עם LLM]
    Q --> S[פורמט: שם דמות + תגובה]
    S --> T[שמירת תגובה ב-State]
    T --> END3([החזרת תגובת הדמות למשתמש])
```

**קיצורים:**
- **Parser** = חילוץ strategy, constraints, confidence מההודעה (LLM בלבד).
- **State** = strategy_selected, constraints_addressed, personas_triggered, round_count וכו'.
- **תנאי סיום** = מספיק סבבים + אסטרטגיה + לפחות 2 דמויות + לפחות 3 אילוצים.

---

## 1. נקודת כניסה (main.py)

```mermaid
flowchart TD
    A[main.py] --> B[בדיקת API key]
    B --> C[validate_api – קריאה מינימלית ל-LLM]
    C --> D[הגדר env: USER_ID, MAX_ROUNDS]
    D --> E[subprocess: streamlit run gui.py]
    E --> F[דפדפן / GUI]
```

## 2. זרימת GUI (gui.py)

```mermaid
flowchart TD
    subgraph GUI
        P[Streamlit מופעל] --> Q[init_session]
        Q --> R{simulation ב-session?}
        R -->|לא| S[SimulationController חדש]
        S --> T[initialize → תרחיש ראשוני]
        T --> U[messages ← הודעת הקשר]
        R -->|כן| V[render_chat]
        U --> V
        V --> W[הצג הודעות צ'אט]
        W --> X[chat_input]
        X --> Y{המשתמש שלח הודעה?}
        Y -->|כן| Z[process_user_input]
        Z --> AA[הצג תשובת agent]
        AA --> AB{should_end?}
        AB -->|כן| AC[simulation_ended = True]
        AC --> AD[קבלת ציון מ-get_last_report]
        AD --> AE{ציון 7+?}
        AE -->|כן| AF[balloons + הודעת הצלחה]
        AE -->|לא| AG{ציון 4–6?}
        AG -->|כן| AH[snow + הודעה בינונית]
        AG -->|לא| AI[הודעת כישלון, ללא אנימציה]
        AF --> AJ{simulation_ended?}
        AH --> AJ
        AI --> AJ
        AB -->|לא| X
        AJ -->|כן| AK[הצגת תוצאה + כפתור Start new simulation]
        AK --> AL{לחיצה?}
        AL -->|כן| AM[ריקון session_state + rerun]
        AM --> Q
        AL -->|לא| X
        Y -->|לא| AJ
    end
```

## 3. ליבת הסימולציה (process_user_input)

```mermaid
flowchart TD
    subgraph SimulationController
        I[process_user_input] --> J[state.add_message user]
        J --> K[round_count += 1]
        K --> L{in_final_review?}
        L -->|כן| M[parser.parse_user_response]
        M --> N[state.update_from_extracted]
        N --> O[evaluate_session]
        O --> P[format_feedback]
        P --> Q[החזר feedback + should_end=True]
        L -->|לא| R[parser.parse_user_response]
        R --> S[state.update_from_extracted]
        S --> T{should_end?}
        T -->|כן| U[in_final_review = True]
        U --> V[format_final_review_message]
        V --> W[החזר הודעת סיכום + False]
        T -->|לא| X[choose_next_persona]
        X --> Y[get_persona_instance]
        Y --> Z[generate_complication]
        Z --> AA[persona.respond_as_persona]
        AA --> AB[החזר תשובה + False]
    end
```

## 4. אתחול סימולציה (initialize)

```mermaid
flowchart LR
    A[scenario_generator] --> B[randomize_variant]
    B --> C[שירותי AWS + הקשר עסקי]
    C --> D[ScenarioPacket]
    D --> E[present_context]
    E --> F[הודעת ברוך הבא + קוד]
```

## 5. פרסור תשובת משתמש (parser)

```mermaid
flowchart TD
    A[parse_user_response] --> B[_parse_with_llm]
    B --> C[JSON: strategy, constraints, confidence]
    C --> D[_normalize_constraints]
    D --> E[החזר extracted]
    E --> F[state.update_from_extracted]
```
(LLM חובה – אין fallback.)

## 6. בחירת דמות ותגובה (personas)

```mermaid
flowchart TD
    A[choose_next_persona] --> B{last_persona?}
    B -->|ריק| C[לפי constraints שחסרים]
    B -->|קיים| D[למעט last_persona]
    C --> E[PM / DevOps / CTO]
    D --> E
    E --> F[get_persona_instance]
    F --> G[generate_complication]
    G --> H[respond_as_persona → LLM]
    H --> I[תשובה מפורמטת]
```
(LLM חובה – אין תגובת template.)

## 7. תנאי סיום והערכה (state + evaluation)

```mermaid
flowchart TD
    A[should_end?] --> B{round_count >= max_rounds?}
    B -->|כן| Z[סיום]
    B -->|לא| C{אסטרטגיה נבחרה?}
    C -->|לא| N[המשך]
    C -->|כן| D{personas >= 2?}
    D -->|לא| N
    D -->|כן| E{constraints >= 3?}
    E -->|לא| N
    E -->|כן| F[in_final_review = True]
    F --> G[הודעת Final Review]
    G --> H[משתמש עונה]
    H --> I[evaluate_session]
    I --> J[format_feedback]
    J --> Z
```

## 8. מבט על כל המערכת

```mermaid
flowchart TB
    subgraph Entry
        M[main.py]
    end
    subgraph UI
        G[gui.py / Streamlit]
    end
    subgraph Core
        SC[SimulationController]
        ST[State]
    end
    subgraph Data
        SCEN[scenario.py]
        PERS[personas.py]
        PARS[parser.py]
        EVAL[evaluation.py]
        CFG[config.py]
    end

    M --> B[בדיקת API + validate_api]
    B --> G
    G --> SC
    SC --> ST
    SC --> SCEN
    SC --> PERS
    SC --> PARS
    SC --> EVAL
    M --> CFG
```

---

*נוצר עבור Cloud Migration Simulation. ניתן להציג דיאגרמות Mermaid ב־GitHub, VS Code (תוסף Markdown Preview Mermaid), או ב־[mermaid.live](https://mermaid.live).*
