import { PlayCircleIcon } from "lucide-react";
import { motion } from "framer-motion";
import { Button } from '@astryxdesign/core/Button';
import { Text } from '@astryxdesign/core/Text';

export default function HeroSection() {

    return (
        <>
            <motion.section className="flex flex-col items-center">
                <motion.div className="flex items-center gap-3 mt-32"
                    initial={{ y: -20, opacity: 0 }}
                    whileInView={{ y: 0, opacity: 1 }}
                    viewport={{ once: true }}
                    transition={{ delay: 0.2, type: "spring", stiffness: 320, damping: 70, mass: 1 }}
                >
                    <p>Voice-first triage. Any phone, no app.</p>
                </motion.div>
                <motion.h1 className="text-center text-4xl/13 md:text-6xl/19 mt-4 font-semibold tracking-tight max-w-3xl"
                    initial={{ y: 50, opacity: 0 }}
                    whileInView={{ y: 0, opacity: 1 }}
                    viewport={{ once: true }}
                    transition={{ type: "spring", stiffness: 240, damping: 70, mass: 1 }}
                >
                    Every phone. Every language. The right care, every time.
                </motion.h1>
                <motion.p className="text-center text-gray-100 text-base/7 max-w-md mt-6"
                    initial={{ y: 50, opacity: 0 }}
                    whileInView={{ y: 0, opacity: 1 }}
                    viewport={{ once: true }}
                    transition={{ delay: 0.2, type: "spring", stiffness: 320, damping: 70, mass: 1 }}
                >
                    Medline AI answers patient calls, tiers symptoms by WHO/IMCI-style rules — emergency, urgent, self-care — and routes to advice, callback, or nearest clinic. Triage + routing, never diagnosis.
                </motion.p>

                <motion.div className="flex flex-col md:flex-row max-md:w-full items-center gap-4 md:gap-3 mt-6"
                    initial={{ y: 50, opacity: 0 }}
                    whileInView={{ y: 0, opacity: 1 }}
                    viewport={{ once: true }}
                    transition={{ type: "spring", stiffness: 320, damping: 70, mass: 1 }}
                >
                    <Button label='Call +256 323 200 717' variant='primary' size='lg' href='tel:+256323200717' as='a' style={{paddingInline: 'var(--spacing-8)', paddingBlock: 'var(--spacing-4)'}} />
                    <Button label='Staff login' variant='secondary' size='lg' icon={<PlayCircleIcon className="size-4.5" />} href='/login' as='a' style={{paddingInline: 'var(--spacing-8)', paddingBlock: 'var(--spacing-4)'}} />
                </motion.div>
            </motion.section>
        </>
    );
}