ALLOWED = %w[Observation Commitment Intention].freeze
def validate(id, kind, causes, known)
  !id.empty? && ALLOWED.include?(kind) && causes.all? { |c| known.include?(c) }
end
abort unless validate("g1", "Observation", [], [])
puts "TRS Ruby technical smoke pass"
