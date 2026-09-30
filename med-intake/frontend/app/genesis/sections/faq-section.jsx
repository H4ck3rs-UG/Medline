import SectionTitle from '../components/section-title';
import { ChevronDownIcon } from 'lucide-react';
import { useState } from 'react';
import { motion } from "framer-motion";

export default function FaqSection() {
    const [isOpen, setIsOpen] = useState(false);
    const data = [
        {
            question: 'Do I need coding or design experience to use PrebuiltUI?',
            answer: "Basic coding knowledge (HTML/CSS, Tailwind) helps, but advanced design skills aren't required. You can use components as-is or customize them.",
        },
        {
            question: 'What is PrebuiltUI and how does it help developers and designers?',
            answer: 'PrebuiltUI provides ready-to-use, customizable UI components and templates, saving time for developers and designers.',
        },
        {
            question: 'Can I use PrebuiltUI components in my existing project?',
            answer: 'Yes, components can be integrated into HTML, React, Next.js, Vue, and other projects using Tailwind CSS.',
        },
        {
            question: 'How customizable are the generated components?',
            answer: 'Components are highly customizable with Tailwind utility classes, theming, and structural adjustments.',
        },
        {
            question: 'Does PrebuiltUI support team collaboration?',
            answer: "There's no clear documentation on built-in collaboration features. Check their support for team options.",
        },
        {
            question: 'Can I try PrebuiltUI before purchasing a plan?',
            answer: 'Yes, you can try PrebuiltUI with full access to features.',
        },
    ];

    return (
        <section className='mt-32'>
            <SectionTitle title="FAQ's" description="Looking for answers to your frequently asked questions? Check out our FAQ's section below to find." />
            <div className='mx-auto mt-12 space-y-4 w-full max-w-xl'>
                {data.map((item, index) => (
                    <motion.div key={index} className='flex flex-col glass rounded-md'
                        initial={{ y: 150, opacity: 0 }}
                        whileInView={{ y: 0, opacity: 1 }}
                        viewport={{ once: true }}
                        transition={{ delay: `${index * 0.15}`, type: "spring", stiffness: 320, damping: 70, mass: 1 }}
                    >
                        <h3 className='flex cursor-pointer hover:bg-white/10 transition items-start justify-between gap-4 p-4 font-medium' onClick={() => setIsOpen(isOpen === index ? null : index)}>
                            {item.question}
                            <ChevronDownIcon className={`size-5 transition-all shrink-0 duration-400 ${isOpen === index ? 'rotate-180' : ''}`} />
                        </h3>
                        <p className={`px-4 text-sm/6 transition-all duration-400 overflow-hidden ${isOpen === index ? 'pt-2 pb-4 max-h-80' : 'max-h-0'}`}>{item.answer}</p>
                    </motion.div>
                ))}
            </div>
        </section>
    );
}