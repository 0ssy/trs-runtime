------------------------------ MODULE TrsCore ------------------------------
EXTENDS Naturals, FiniteSets

CONSTANTS MaxRecords

RecordIds == 1..MaxRecords

\* Record dependency shape:
\* 1=root, 2=cap, 3=ia, 4=ib, 5=ca, 6=cb, 7=cla, 8=clb
Causes == [
  r \in RecordIds |->
    IF r = 1 THEN {}
    ELSE IF r = 2 THEN {1}
    ELSE IF r = 3 THEN {1}
    ELSE IF r = 4 THEN {1}
    ELSE IF r = 5 THEN {1, 3}
    ELSE IF r = 6 THEN {1, 4}
    ELSE IF r = 7 THEN {3, 5}
    ELSE IF r = 8 THEN {4, 6}
    ELSE {}
]

Auth == [
  r \in RecordIds |->
    IF r = 5 THEN {2}
    ELSE IF r = 6 THEN {2}
    ELSE {}
]

VARIABLES LogA, LogB

Init ==
  /\ LogA = {}
  /\ LogB = {}

Appendable(log, r) ==
  /\ r \in RecordIds
  /\ r \notin log
  /\ Causes[r] \subseteq log
  /\ Auth[r] \subseteq log

AppendA(r) ==
  /\ Appendable(LogA, r)
  /\ LogA' = LogA \cup {r}
  /\ UNCHANGED LogB

AppendB(r) ==
  /\ Appendable(LogB, r)
  /\ LogB' = LogB \cup {r}
  /\ UNCHANGED LogA

SyncAToB(r) ==
  /\ r \in LogA
  /\ r \notin LogB
  /\ Causes[r] \subseteq LogB
  /\ Auth[r] \subseteq LogB
  /\ LogB' = LogB \cup {r}
  /\ UNCHANGED LogA

SyncBToA(r) ==
  /\ r \in LogB
  /\ r \notin LogA
  /\ Causes[r] \subseteq LogA
  /\ Auth[r] \subseteq LogA
  /\ LogA' = LogA \cup {r}
  /\ UNCHANGED LogB

Next ==
  \E r \in RecordIds :
    AppendA(r) \/ AppendB(r) \/ SyncAToB(r) \/ SyncBToA(r)

Spec ==
  Init /\ [][Next]_<<LogA, LogB>>

CausalClosure(log) ==
  \A r \in log : Causes[r] \subseteq log /\ Auth[r] \subseteq log

LocalQuiescent(log) ==
  \A r \in RecordIds : ~(Appendable(log, r))

ConflictVisible(log) ==
  ~LocalQuiescent(log) \/ ~({3, 4} \subseteq log) \/ {5, 6} \subseteq log

ClosureSatisfied(log) ==
  ~LocalQuiescent(log) \/ ~({3, 4} \subseteq log) \/ {7, 8} \subseteq log

Quiescent(logL, logR) ==
  /\ \A r \in RecordIds : ~(Appendable(logL, r))
  /\ \A r \in RecordIds : ~(Appendable(logR, r))
  /\ \A r \in logL \ logR : ~(Causes[r] \subseteq logR /\ Auth[r] \subseteq logR)
  /\ \A r \in logR \ logL : ~(Causes[r] \subseteq logL /\ Auth[r] \subseteq logL)

NoDuplicateIds ==
  /\ Cardinality(LogA) <= MaxRecords
  /\ Cardinality(LogB) <= MaxRecords

CausalClosureA == CausalClosure(LogA)
CausalClosureB == CausalClosure(LogB)
ConflictVisibleA == ConflictVisible(LogA)
ConflictVisibleB == ConflictVisible(LogB)
ClosureA == ClosureSatisfied(LogA)
ClosureB == ClosureSatisfied(LogB)
QuiescentConverges ==
  ~(Quiescent(LogA, LogB)) \/ (LogA = LogB)

=============================================================================
