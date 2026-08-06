import Foundation
func validate(_ id:String,_ kind:String,_ causes:[String],_ known:Set<String>)->Bool { !id.isEmpty && ["Observation","Commitment","Intention"].contains(kind) && causes.all { known.contains($0) } }
precondition(validate("g1","Observation",[],[])); print("TRS Swift technical smoke pass")
