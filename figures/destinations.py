from traceroute import RouteSamples, load_samples


DestinationSamples = dict[str, RouteSamples]


def get_destination_samples() -> DestinationSamples:
    destinations = ["melbourne", "osaka", "oxford", "stanford"]

    destination_samples: dict[str, RouteSamples] = {
        destination: load_samples(f"samples/{destination}.samples")
        for destination in destinations
    }

    return destination_samples
