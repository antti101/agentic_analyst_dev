# main_simple.py - Simplified CLI for direct semantic layer interaction

import argparse
import json
from .config_loader import config
from .semantic_layer_mcp import DataPlatformApp

def main():
    """Main function to run the application without AutoGen."""
    parser = argparse.ArgumentParser(description='Cube Analyst - Semantic Layer CLI Tool')
    parser.add_argument('--file', type=str, help='Path to a semantic layer file (overrides config.yaml)')
    parser.add_argument('--search', type=str, help='Search for measures or dimensions')
    parser.add_argument('--cube', type=str, help='Get details for a specific cube (e.g., Orders, Goods)')
    parser.add_argument('--cubes', action='store_true', help='List all available cubes')
    parser.add_argument('--measures', type=str, nargs='?', const='all', help='List measures, optionally filtered by cube')
    parser.add_argument('--dimensions', type=str, nargs='?', const='all', help='List dimensions, optionally filtered by cube')

    args = parser.parse_args()

    # Initialize app with the correct semantic layer file
    file_path = args.file if args.file else config.get("semantic_layer.file_path", "assets/semantic_layer.txt")
    print(f"Loading semantic layer from: {file_path}\n")
    try:
        app = DataPlatformApp(file_path)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Please ensure the file path in config.yaml is correct or use the --file argument.")
        return

    if args.search:
        print(f"Searching for: '{args.search}'")
        results = app.semantic_server.search_semantic_items(query=args.search)
        print(json.dumps(results, indent=2))

    elif args.cube:
        print(f"Getting details for cube: {args.cube}")
        results = app.semantic_server.get_cube_details(cube_name=args.cube)
        print(json.dumps(results, indent=2))

    elif args.cubes:
        print("Available Cubes:")
        results = app.semantic_server.get_cubes()
        print(json.dumps(results, indent=2))

    elif args.measures:
        cube_filter = None if args.measures == 'all' else args.measures
        print(f"Listing measures{f' for cube: {cube_filter}' if cube_filter else ''}...")
        results = app.semantic_server.get_measures(cube_name=cube_filter)
        print(json.dumps(results, indent=2))

    elif args.dimensions:
        cube_filter = None if args.dimensions == 'all' else args.dimensions
        print(f"Listing dimensions{f' for cube: {cube_filter}' if cube_filter else ''}...")
        results = app.semantic_server.get_dimensions(cube_name=cube_filter)
        print(json.dumps(results, indent=2))

    else:
        # Interactive mode
        print("=== Cube Analyst Interactive Mode (Simple) ===")
        print("Examples: cubes, cube Orders, search sales, measures Goods, dimensions Buyer")
        print("Type 'quit' or 'exit' to end.")
        print()

        while True:
            try:
                command_str = input("> ").strip()
                if command_str.lower() in ['quit', 'exit', 'q']:
                    break
                if not command_str:
                    continue

                parts = command_str.split()
                command = parts[0].lower()
                args = parts[1:]

                if command == 'cubes':
                    print(json.dumps(app.semantic_server.get_cubes(), indent=2))
                elif command == 'cube' and args:
                    print(json.dumps(app.semantic_server.get_cube_details(args[0]), indent=2))
                elif command == 'search' and args:
                    print(json.dumps(app.semantic_server.search_semantic_items(" ".join(args)), indent=2))
                elif command == 'measures':
                    cube = args[0] if args else None
                    print(json.dumps(app.semantic_server.get_measures(cube), indent=2))
                elif command == 'dimensions':
                    cube = args[0] if args else None
                    print(json.dumps(app.semantic_server.get_dimensions(cube), indent=2))
                else:
                    print("Unknown command. Available: cubes, cube <name>, search <term>, measures [cube], dimensions [cube]")

            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
