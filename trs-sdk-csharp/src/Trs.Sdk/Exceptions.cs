namespace Trs.Sdk;

public class TrsException : Exception
{
    public TrsException(string message, Exception? innerException = null) : base(message, innerException) { }
}

public sealed class TrsConnectionException : TrsException
{
    public TrsConnectionException(string message, Exception? innerException = null) : base(message, innerException) { }
}

public sealed class TrsValidationException : TrsException
{
    public IReadOnlyList<string> Errors { get; }

    public TrsValidationException(string message, IReadOnlyList<string> errors) : base(message)
    {
        Errors = errors;
    }
}

public sealed class TrsServerException : TrsException
{
    public TrsServerException(string message) : base(message) { }
}

public sealed class TrsProtocolException : TrsException
{
    public TrsProtocolException(string message) : base(message) { }
}

