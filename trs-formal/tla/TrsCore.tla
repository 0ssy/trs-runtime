------------------------------ MODULE TrsCore ------------------------------
EXTENDS Naturals, Sequences

CONSTANTS MaxRecords

VARIABLES Log

Record == [id: Nat, causes: SUBSET Nat]

Init ==
  /\ Log = << >>

Ids(seq) == { seq[i].id : i \in 1..Len(seq) }

Appendable(r) ==
  /\ r.id \notin Ids(Log)
  /\ \A c \in r.causes : c \in Ids(Log)

AppendRecord(r) ==
  /\ Appendable(r)
  /\ Log' = Append(Log, r)

Next ==
  \E r \in [id: 1..MaxRecords, causes: SUBSET (1..MaxRecords)] :
    AppendRecord(r)

Spec == Init /\ [][Next]_Log

NoDuplicateIds ==
  \A i, j \in 1..Len(Log) : i # j => Log[i].id # Log[j].id

CausalClosure ==
  \A i \in 1..Len(Log) :
    \A c \in Log[i].causes : c \in { Log[k].id : k \in 1..(i-1) }

=============================================================================
