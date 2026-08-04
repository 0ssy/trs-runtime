module TrsSdk
  class TrsError < StandardError; end
  class TrsConnectionError < TrsError; end
  class TrsValidationError < TrsError
    attr_reader :errors
    def initialize(message, errors = [])
      @errors = errors
      super(message)
    end
  end
  class TrsServerError < TrsError; end
  class TrsProtocolError < TrsError; end
end

