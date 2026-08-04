<?php

namespace TrsSdk;

class TrsException extends \RuntimeException {}

class TrsConnectionError extends TrsException {}

class TrsValidationError extends TrsException
{
    /** @var string[] */
    private array $errors;

    /** @param string[] $errors */
    public function __construct(string $message, array $errors = [])
    {
        parent::__construct($message);
        $this->errors = $errors;
    }

    /** @return string[] */
    public function errors(): array
    {
        return $this->errors;
    }
}

class TrsServerError extends TrsException {}

class TrsProtocolError extends TrsException {}

