import Button from "@/components/ui/Button";

export default function TestPage() {
    return (
        <div className="bg_black min-h-screen flex flex-col p-10 gap-6">
            <h1 className="text-2xl font-bold text-primary-text">Button Test</h1>

            <div className="flex gap-4 items-center">
                <Button variant="primary">Generate Material</Button>
                
                <Button variant="secondary">Cancel</Button>

                <Button variant="primary" isLoading>
                    Generating...
                </Button>

                <Button variant="primary" className="w-64">
                    Wide Button
                </Button>
            </div>
        </div>
    )
}