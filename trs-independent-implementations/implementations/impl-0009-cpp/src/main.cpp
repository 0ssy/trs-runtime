#include <iostream>
#include <set>
#include <string>
#include <vector>
bool validate(const std::string& id,const std::string& kind,const std::vector<std::string>& causes,const std::set<std::string>& known){ if(id.empty() || (kind!="Observation"&&kind!="Commitment"&&kind!="Intention")) return false; for(const auto& c:causes) if(!known.count(c)) return false; return true; }
int main(){ if(!validate("g1","Observation",{},{})) return 1; std::cout<<"TRS C++ technical smoke pass\n"; }
