from figures.destinations import DestinationSamples
from traceroute import RouterResponse


def assert_all_samples_have_same_length(
    destination_samples: DestinationSamples,
) -> None:
    assert all(
        len(route) == len(destination_samples[destination][0])
        for destination, samples in destination_samples.items()
        for route in samples
    )


def assert_always_the_same_IP_for_each_TTL(
    destination_samples: DestinationSamples,
) -> None:
    assert all(
        len(
            set(
                response.ip
                for route in samples
                if isinstance(response := route[ttl - 1], RouterResponse)
            )
        )
        <= 1
        for samples in destination_samples.values()
        for ttl in range(1, len(samples[0]))
    )
