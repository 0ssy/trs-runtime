using System;
using System.Collections.Generic;
static class Program { static bool Validate(string id,string kind,List<string> causes,HashSet<string> known) { return id.Length>0 && (kind=="Observation"||kind=="Commitment"||kind=="Intention") && causes.TrueForAll(known.Contains); } static void Main(){ if(!Validate("g1","Observation",new List<string>(),new HashSet<string>())) throw new Exception(); Console.WriteLine("TRS C# technical smoke pass"); } }
