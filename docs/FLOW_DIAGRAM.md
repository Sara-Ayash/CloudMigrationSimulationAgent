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
    O --> P{LLM זמין?}
    P -->|כן| Q[persona.respond_as_persona עם LLM]
    P -->|לא| R[תגובת template]
    Q --> S[פורמט: שם דמות + תגובה]
    R --> S
    S --> T[שמירת תגובה ב-State]
    T --> END3([החזרת תגובת הדמות למשתמש])
```

**קיצורים:**
- **Parser** = חילוץ strategy, constraints, confidence מההודעה (LLM או rule-based).
- **State** = strategy_selected, constraints_addressed, personas_triggered, round_count וכו'.
- **תנאי סיום** = מספיק סבבים + אסטרטגיה + לפחות 2 דמויות + לפחות 3 אילוצים.

---

## 1. נקודת כניסה (main.py)

```mermaid
flowchart TD
    A[main.py] --> B{--gui?}
    B -->|כן| C[הגדר env: USER_ID, MAX_ROUNDS]
    C --> D[subprocess: streamlit run gui.py]
    D --> E[דפדפן / GUI]
    B -->|לא| F[main_cli]
    F --> G[CLI loop]
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
        AC --> AD[balloons]
        AB -->|לא| X
        AD --> AE{simulation_ended?}
        AE -->|כן| AF[כפתור: Start new simulation]
        AF --> AG{לחיצה?}
        AG -->|כן| AH[ריקון session_state + rerun]
        AH --> Q
        AG -->|לא| X
        Y -->|לא| AE
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
    A[parse_user_response] --> B{LLM זמין?}
    B -->|כן| C[_parse_with_llm]
    C --> D[JSON: strategy, constraints, confidence]
    D --> E[_normalize_constraints]
    E --> F[החזר extracted]
    B -->|לא / שגיאה| G[_parse_rule_based]
    G --> H[מילות מפתח: time, cost, security...]
    H --> F
    F --> I[state.update_from_extracted]
```

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
    G --> H{LLM זמין?}
    H -->|כן| I[respond_as_persona → LLM]
    H -->|לא| J[template response]
    I --> K[תשובה מפורמטת]
    J --> K
```

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
        C[cli.py]
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
    end

    M -->|--gui| G
    M -->|default| C
    G --> SC
    C --> SC
    SC --> ST
    SC --> SCEN
    SC --> PERS
    SC --> PARS
    SC --> EVAL
---

*נוצר עבור Cloud Migration Simulation. ניתן להציג דיאגרמות Mermaid ב־GitHub, VS Code (תוסף Markdown Preview Mermaid), או ב־[mermaid.live](https://mermaid.live).*
