fun validate(id:String, kind:String, causes:List<String>, known:Set<String>) = id.isNotEmpty() && kind in setOf("Observation","Commitment","Intention") && causes.all { it in known }
fun main(){ check(validate("g1","Observation",emptyList(),emptySet())); println("TRS Kotlin technical smoke pass") }
