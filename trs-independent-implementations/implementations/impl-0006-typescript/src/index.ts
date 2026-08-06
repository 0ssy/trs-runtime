export function validate(id: string, kind: string, causes: string[], known: Set<string>): boolean { return id.length > 0 && ["Observation","Commitment","Intention"].includes(kind) && causes.every(c => known.has(c)); }
if (!validate("g1", "Observation", [], new Set())) throw new Error("invalid");
console.log("TRS TypeScript technical smoke pass");
